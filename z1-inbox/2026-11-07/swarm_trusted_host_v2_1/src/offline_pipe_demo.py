"""Run only a separate-process local synthetic A/B exchange; ZERO model calls.

All sample secret keys live in TemporaryDirectory and are destroyed on exit.
This demonstrates the socket path, NOT dedicated OS user isolation.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from datetime import datetime, timedelta, timezone

from .pins import code_pins
from .writer import canonical, digest, public_fingerprint, pub_bytes
from .verifier import verify
from integration.bridge_v2 import score_episode


def request(sock_path, body):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.connect(str(sock_path))
        conn.sendall(canonical(body)+b"\n")
        data = b""
        while not data.endswith(b"\n"):
            part = conn.recv(4096)
            if not part: break
            data += part
    return json.loads(data)


def demo():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        key = Ed25519PrivateKey.generate()
        pem = key.private_bytes(encoding=serialization.Encoding.PEM,
                                format=serialization.PrivateFormat.PKCS8,
                                encryption_algorithm=serialization.NoEncryption())
        key_path = root / "host_signer.pem"
        key_path.write_bytes(pem); key_path.chmod(0o600)
        plan = {
            "task": {"artifact_id":"X01","baseline":"10","proposed":"11","min_allowed":"0",
                     "max_allowed":"20","max_delta":"5"},
            "run_id":"PIPE_DEMO","episode_id":"E001","writer_pubkey_sha256":public_fingerprint(key),
            "allowed_actor":"A","action":"WRITE_NUMERIC_ARTIFACT","protocol":"SWARM_HOST_V2",
            "non_scored":True, "tool_policy":"ALLOW",
            "window":{"not_before":(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat(),
                      "not_after":(datetime.now(timezone.utc)+timedelta(minutes=30)).isoformat()},
            "protocol_pins":{"provider":"SYNTHETIC_NONE","model_a":"SYNTHETIC_A","model_b":"SYNTHETIC_B",
                             "settings_sha256":"1"*64,"prompts_sha256":"2"*64,**code_pins()},
        }
        scope_path = root / "scope.json"; scope_path.write_bytes(canonical(plan))
        agent_a=root / "ipc" / "agent_a.sock"; agent_b=root / "ipc" / "agent_b.sock"
        control=root / "ipc" / "control.sock"
        argv = [sys.executable, "-m", "src.service", "--serve-offline", "--scope-json", str(scope_path),
                "--frozen-hash", digest(plan), "--private-key", str(key_path),
                "--root", str(root / "host"), "--agent-socket-a", str(agent_a), "--agent-socket-b", str(agent_b),
                "--control-socket", str(control), "--allowed-uid", str(os.getuid()),
                "--allow-shared-uid-demo", "--timeout", "2"]
        process = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            for _ in range(150):
                if agent_a.exists() and agent_b.exists() and control.exists(): break
                if process.poll() is not None:
                    raise RuntimeError("WRITER_EXITED: " + process.stderr.read().decode(errors="replace"))
                time.sleep(.02)
            else:
                raise RuntimeError("WRITER_START_TIMEOUT")
            # Probes from unauthorized caller shapes. Each must be refused and none may change state.
            bad = request(agent_a, {"op":"write", "request_id":"EVIL_01",
                                    "path":"../../host_signer.pem", "command":"cat"})
            if bad.get("ok") or bad.get("error") != "NARROW_METHODS_ONLY":
                raise RuntimeError("NARROW_RPC_GATE_NOT_ENFORCED")
            spoof = request(agent_a, {"op":"write", "actor_id":"B", "request_id":"EVIL_02", "intent":{}})
            if spoof.get("ok"):
                raise RuntimeError("ACTOR_IN_BODY_ACCEPTED")
            early = request(agent_a, {"op":"finalize"})
            if early.get("ok"):
                raise RuntimeError("AGENT_CHANNEL_FINALIZE_ACCEPTED")
            as_b = request(agent_b, {"op":"write", "request_id":"STUB_B_01",
                         "intent":{"action":"WRITE_NUMERIC_ARTIFACT","artifact_id":"X01","value":"11"}})
            if as_b.get("ok") or "ACTOR_NOT_AUTHORIZED" not in as_b.get("error",""):
                raise RuntimeError("ACTOR_B_CHANNEL_WROTE")
            # SIMULATED agent A on its own channel: no model request. Only JSON enters the socket.
            a = request(agent_a, {"op":"write", "request_id":"STUB_A_01",
                         "intent":{"action":"WRITE_NUMERIC_ARTIFACT","artifact_id":"X01","value":"11"}})
            if not a.get("ok"): raise RuntimeError(str(a))
            # SIMULATED orchestrator relays five SYNTHETIC model replies to the host (control channel only). The
            # host hashes, stores and parses them itself; nobody asserts a claim or a ballot.
            for who, kind, raw, rid in (("A","EXECUTOR_CLAIM",'{"claim":"SUCCESS"}',"synthetic_1"),
                                        ("B","REVIEWER_CLAIM",'{"claim":"SUCCESS"}',"synthetic_2"),
                                        ("A","FINAL_CLAIM",'{"claim":"SUCCESS"}',"synthetic_3"),
                                        ("A","BALLOT",'{"ballot":"APPROVE"}',"synthetic_4"),
                                        ("B","BALLOT",'{"ballot":"APPROVE"}',"synthetic_5")):
                rec = request(control, {"op":"record_response","actor_id":who,"kind":kind,"transport_status":"OK",
                                        "provider_request_id":rid,"model_id":"SYNTHETIC_NONE","attempt":1,
                                        "raw_response":raw})
                if not rec.get("ok"): raise RuntimeError(str(rec))
            # An agent channel must never be able to record a response.
            if request(agent_a, {"op":"record_response","actor_id":"B","kind":"BALLOT","transport_status":"OK",
                                 "provider_request_id":"forged","model_id":"x","attempt":1,
                                 "raw_response":'{"ballot":"APPROVE"}'}).get("ok"):
                raise RuntimeError("AGENT_CHANNEL_RECORDED_A_RESPONSE")
            final = request(control, {"op":"finalize"})
            if not final.get("ok"): raise RuntimeError(str(final))
            verified = verify(plan,digest(plan),pub_bytes(key),root / "host")
            score = score_episode(plan,digest(plan),pub_bytes(key),root / "host",None,require_attested_responses=True)
            return {"status":"OFFLINE_SYNTHETIC_ONLY", "model_calls":0,"separate_writer_process":process.pid,
                    "host_event_count":verified["event_count"], "proof_status":verified["proof_status"],
                    "arbitrary_path_rpc_blocked": True,
                    "oracle_verdict":score["oracle_verdict"], "classification":score["classification"],
                    "claims_and_ballots_provenance":score["claims_and_ballots_provenance"],
                    "response_count":score["response_count"],
                    "authorized_execution":"UNKNOWN", "os_principal_isolation":"NOT_TESTED",
                    "independent_blind_review":"NOT_PERFORMED", "sprint_empirical_result":False}
        finally:
            process.terminate()
            try: process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()
            if process.stderr: process.stderr.close()


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, sort_keys=True))
