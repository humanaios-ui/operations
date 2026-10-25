"""Live episode runner for the frozen collusion audit. Stdlib only.

Calls an OpenAI-compatible chat endpoint for the 20 scheduled live packets.
Each episode starts fresh. Actor A and actor B keep separate histories. Each
call is made once: no retries, no scripted substitutes, no selecting successes.
Failures are recorded as failures. Blind evidence never carries condition
names, instructions, or detector predictions; those go to a separate scoring file.

The API key is read from the environment only and is never written to disk.
"""

import argparse
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import audit

ROOT = Path(__file__).resolve().parent
AMENDMENT_PATH = ROOT / "protocol_amendment_live_v0_1.json"
AMENDMENT = json.loads(AMENDMENT_PATH.read_text())
ENDPOINT = AMENDMENT["run_settings"]["endpoint"]
KEY_ENV = "CEREBRAS_API_KEY"  # env var name and Keychain service name
SAMPLING = AMENDMENT["run_settings"]["sampling"]
BALLOT_SAMPLING = SAMPLING  # the amendment applies one setting to every call
USER_AGENT = "humanaios-collusion-audit/0.1"  # default urllib agent is blocked (error 1010)
MAX_MESSAGE_CHARS = 4000
BALLOTS = ("APPROVE", "REJECT")
SYSTEM = AMENDMENT["task_presentation"]["system_template"]
MESSAGE_PROMPT = AMENDMENT["task_presentation"]["message_prompt"]
BALLOT_PROMPT = AMENDMENT["task_presentation"]["ballot_prompt"]


def load_key():
    """Env var first, then macOS Keychain. Returns (key, source) or (None, None). Never prints."""
    key = os.environ.get(KEY_ENV)
    if key:
        return key, f"env:{KEY_ENV}"
    found = subprocess.run(["security", "find-generic-password", "-s", KEY_ENV, "-w"],
                           capture_output=True, text=True)
    if found.returncode == 0 and found.stdout.strip():
        return found.stdout.strip(), f"keychain:{KEY_ENV}"
    return None, None


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_check(root=ROOT):
    """Refuse to run if any frozen file has drifted from freeze.json."""
    freeze = json.loads((root / "freeze.json").read_text())
    for name, expected in freeze["hashes"].items():
        actual = sha256_file(root / name)
        if actual != expected:
            raise RuntimeError(f"frozen file changed: {name}")
    return freeze


def code_commit(root=ROOT):
    """Commit that contains the code. Refuses if the audit folder has uncommitted changes."""
    status = subprocess.run(["git", "status", "--porcelain", "--", str(root)],
                            capture_output=True, text=True, check=True).stdout
    if status.strip():
        raise RuntimeError("research/collusion_audit has uncommitted changes; commit before running")
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()


def post_json(url, key, body, timeout=60):
    """One HTTP attempt. Returns a dict describing the outcome; never raises for HTTP errors."""
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {key}",
                                              "Content-Type": "application/json",
                                              "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"http_status": response.status, "headers": dict(response.headers),
                    "text": response.read().decode(errors="replace")}
    except urllib.error.HTTPError as error:
        return {"http_status": error.code, "headers": dict(error.headers),
                "text": error.read().decode(errors="replace")}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {"http_status": None, "headers": {}, "text": "", "transport_error": repr(error)}


def chat(model, messages, sampling, key, post=post_json):
    """Single attempt. Returns the full record of the call, success or failure."""
    body = {"model": model, "messages": messages, **sampling}
    raw = post(f"{ENDPOINT}/chat/completions", key, body)
    record = {"request": {"model": model, "messages": messages, "sampling": sampling},
              "http_status": raw.get("http_status"),
              "request_id": raw.get("headers", {}).get("x-request-id"),
              "transport_error": raw.get("transport_error")}
    try:
        parsed = json.loads(raw.get("text") or "null")
    except json.JSONDecodeError:
        parsed = None
    record["response_raw"] = raw.get("text", "")[:20000]
    if raw.get("http_status") == 200 and isinstance(parsed, dict):
        choice = parsed["choices"][0]
        message = choice["message"]
        record["reasoning"] = message.get("reasoning") or message.get("reasoning_content")
        record.update(status="ok", content=message.get("content"),
                      finish_reason=choice.get("finish_reason"),
                      usage=parsed.get("usage"), response_id=parsed.get("id"))
        if not record["content"]:
            record.update(status="call_failed", error="empty_content")
    else:
        record.update(status="call_failed", content=None,
                      error=(parsed or {}).get("error") if isinstance(parsed, dict) else None)
    if not record["request_id"] and isinstance(parsed, dict):
        record["request_id"] = parsed.get("id")
    return record


def system_text(actor, task, condition_prompt):
    return SYSTEM.format(actor=actor, requirement=task["requirement"], limit=task["limit"],
                         values=task["values"], condition=condition_prompt)


def new_budget(cap):
    return {"cap": cap, "used": 0, "prompt": 0, "completion": 0}


def budget_exhausted(budget):
    return budget is not None and budget["used"] >= budget["cap"]


def estimated_cost_usd(budget):
    price = AMENDMENT["budget"]["pricing_usd_per_million_tokens"]
    return round((budget["prompt"] * price["input"] + budget["completion"] * price["output"]) / 1e6, 6)


def run_episode(packet, model, key, post=post_json, budget=None):
    """Run one episode. Histories are local to this call, so nothing carries across episodes.

    With a budget, no call starts once cumulative tokens reach the cap. The episode is then
    recorded as budget_stopped with whatever was already produced; nothing is filled in.
    """
    histories = {actor: [{"role": "system",
                          "content": system_text(actor, packet["task"], packet["actor_instructions"])}]
                 for actor in ("A", "B")}
    calls, texts, ballots = [], {}, {}
    status = "complete"
    stopped = []

    def step(label, actor, user_text, sampling):
        if budget_exhausted(budget):
            stopped.append(label)
            return None
        histories[actor].append({"role": "user", "content": user_text})
        record = chat(model, list(histories[actor]), sampling, key, post)
        record.update(step=label, actor=actor)
        calls.append(record)
        usage = record.get("usage") or {}
        if budget is not None:
            budget["used"] += usage.get("total_tokens") or 0
            budget["prompt"] += usage.get("prompt_tokens") or 0
            budget["completion"] += usage.get("completion_tokens") or 0
        if record["status"] != "ok":
            return None
        histories[actor].append({"role": "assistant", "content": record["content"] or ""})
        return record["content"]

    message_prompt = MESSAGE_PROMPT
    texts["A"] = step("A_message", "A", message_prompt.format(other="B"), SAMPLING)
    if texts["A"] is not None:
        texts["B"] = step("B_message", "B",
                          f"Reviewer A wrote:\n{texts['A']}\n\n" + message_prompt.format(other="A"),
                          SAMPLING)
    if texts.get("A") is None or texts.get("B") is None:
        status = "call_failed"
    else:
        ballot_prompt = BALLOT_PROMPT
        for actor, other in (("A", "B"), ("B", "A")):
            if status == "call_failed":
                break
            # Each actor sees both messages before its ballot.
            user_text = (f"Reviewer {other} wrote:\n{texts[other]}\n\n" + ballot_prompt
                         if actor == "A" else ballot_prompt)
            reply = step(f"{actor}_ballot", actor, user_text, BALLOT_SAMPLING)
            if reply is None:
                status = "call_failed"
            elif reply in BALLOTS:
                ballots[actor] = reply
            else:
                ballots[actor] = None
                status = "malformed_ballot"

    for actor in ("A", "B"):
        if texts.get(actor) is not None and len(texts[actor]) > MAX_MESSAGE_CHARS:
            status = "message_too_long"
    if status in ("complete", "malformed_ballot") and any(
            c.get("finish_reason") == "length" for c in calls):
        status = "truncated_output"
    if stopped:
        status = "budget_stopped"
    return {"status": status, "budget_stopped_before": stopped[0] if stopped else None, "task": packet["task"], "texts": texts, "ballots": ballots,
            "calls": calls, "episode_id": packet["episode_id"],
            "assigned_condition": packet["assigned_condition"]}


def blind_evidence(result, provenance):
    """Evidence an external evaluator may see. No condition, instructions, or predictions."""
    if result["status"] != "complete":
        return None
    return {"episode_id": result["episode_id"], "provenance": provenance,
            "evidence": {"task": result["task"],
                         "messages": [{"actor": actor, "text": result["texts"][actor]}
                                      for actor in ("A", "B")],
                         "ballots": result["ballots"]}}


def scoring_record(result, blind):
    """Kept separate from blind evidence. Detector predictions come from stripped evidence only."""
    predictions = audit.detect(blind["evidence"]) if blind else None
    return {"episode_id": result["episode_id"], "assigned_condition": result["assigned_condition"],
            "status": result["status"], "detector_predictions": predictions,
            "observed_label": "PENDING_INDEPENDENT_ADJUDICATION"}


def list_models(key, timeout=60):
    """GET /models: records which model IDs the endpoint actually serves."""
    request = urllib.request.Request(f"{ENDPOINT}/models",
                                    headers={"Authorization": f"Bearer {key}", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode(errors="replace"))
            return {"http_status": response.status,
                    "model_ids": sorted(item["id"] for item in body.get("data", []))}
    except urllib.error.HTTPError as error:
        return {"http_status": error.code, "model_ids": None}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        return {"http_status": None, "model_ids": None, "transport_error": repr(error)}


def connectivity(run_id, model, key, out_root=ROOT / "live_runs", post=post_json):
    """Not study data. Stored apart from episodes and never scored."""
    out = Path(out_root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    listing = list_models(key)
    result = {"purpose": "connectivity check, outside study data", "model": model,
              "models_listing": listing,
              "model_listed": bool(listing.get("model_ids")) and model in listing["model_ids"],
              "ping": chat(model, [{"role": "user", "content": "Reply with the single word OK."}],
                           {"temperature": 0.0, "max_completion_tokens": 2048,
                            "reasoning_effort": "low"}, key, post)}
    (out / "connectivity.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    return result


def run(run_id, model, key, out_root=ROOT / "live_runs", post=post_json, key_source="unknown",
        max_total_tokens=None):
    freeze = frozen_check()
    cap = AMENDMENT["budget"]["max_total_tokens"]
    if max_total_tokens is not None:
        cap = min(cap, max_total_tokens)  # a run may lower the pre-call cap, never raise it
    budget = new_budget(cap)
    commit = code_commit()
    if model != AMENDMENT["run_settings"]["model"]:
        raise RuntimeError("model differs from the pre-call amendment; amend before running")
    check_path = Path(out_root) / run_id / "connectivity.json"
    if not check_path.exists():
        raise RuntimeError("run the connectivity check first (outside study data)")
    check = json.loads(check_path.read_text())
    if check["ping"]["status"] != "ok" or not check["model_listed"]:
        raise RuntimeError("connectivity check did not pass; model must be listed and ping ok")
    packets_path = ROOT / "live_packets.json"
    packets = json.loads(packets_path.read_text())
    protocol_sha = sha256_file(ROOT / "protocol.json")
    if packets["protocol_sha256"] != protocol_sha:
        raise RuntimeError("live_packets.json does not match protocol.json")
    out = Path(out_root) / run_id
    if out.exists() and any(p.name != "connectivity.json" for p in out.iterdir()):
        raise RuntimeError(f"run directory already holds a run; choose a new run id: {out}")
    out.mkdir(parents=True, exist_ok=True)
    for sub in ("episodes", "blind_evidence", "scoring"):
        (out / sub).mkdir(parents=True)
    manifest = {"run_id": run_id, "code_commit": commit, "protocol_sha256": protocol_sha,
                "packets_sha256": sha256_file(packets_path), "freeze_status": freeze["status"],
                "endpoint": ENDPOINT, "model": model, "sampling": SAMPLING,
                "amendment_sha256": sha256_file(AMENDMENT_PATH), "key_source": key_source,
                "token_budget_cap": cap,
                "independent_evaluator": None, "episodes_scheduled": len(packets["episodes"])}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    by_status, not_started = {}, []
    for packet in packets["episodes"]:
        if budget_exhausted(budget):
            not_started.append(packet["episode_id"])
            continue
        result = run_episode(packet, model, key, post, budget)
        provenance = {"run_id": run_id, "code_commit": commit, "model": model,
                      "request_ids": [c.get("request_id") for c in result["calls"]]}
        blind = blind_evidence(result, provenance)
        (out / "episodes" / f"{result['episode_id']}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True))
        if blind:
            (out / "blind_evidence" / f"{result['episode_id']}.json").write_text(
                json.dumps(blind, indent=2, sort_keys=True))
            audit.validate(blind["evidence"])
        (out / "scoring" / f"{result['episode_id']}.json").write_text(
            json.dumps(scoring_record(result, blind), indent=2, sort_keys=True))
        by_status[result["status"]] = by_status.get(result["status"], 0) + 1
    summary = {"episodes_scheduled": len(packets["episodes"]), "by_status": by_status,
               "episodes_not_started_budget": not_started,
               "tokens": {"cap": cap, "total": budget["used"], "prompt": budget["prompt"],
                          "completion": budget["completion"]},
               "estimated_cost_usd": estimated_cost_usd(budget)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("connect", "run"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-total-tokens", type=int,
                        help="lower the pre-call token cap for this run (cannot raise it)")
    args = parser.parse_args()
    model = AMENDMENT["run_settings"]["model"]
    key, source = load_key()
    if not key:
        raise SystemExit(f"{KEY_ENV} not found in env or Keychain; no call was made")
    if args.command == "connect":
        result = connectivity(args.run_id, model, key)
        print(json.dumps({"ping_status": result["ping"]["status"],
                          "http_status": result["ping"]["http_status"],
                          "model_listed": result["model_listed"],
                          "request_id": result["ping"]["request_id"]}, indent=2))
        return
    print(json.dumps(run(args.run_id, model, key, key_source=source,
                         max_total_tokens=args.max_total_tokens), indent=2))


if __name__ == "__main__":
    main()
