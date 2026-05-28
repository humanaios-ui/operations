#!/usr/bin/env python3
"""
HAIOS Pipeline Coordinator — v1.0
Builder v1.7 compliant · Step 10 engine
HumanAIOS · S-052026-01

The pipeline coordinator is the Step 10 mechanism: continuous automated
inventory that runs on every system touchpoint, passes outputs forward
as inputs, handles errors at each stage, and surfaces results for
Night's review via #acat-monitor.

Design principle: AI eats friction. Humans eat conscience.
The coordinator handles sequence and data flow.
Zone 2 decisions (DAILY_WILL_QUERY, Z2_MOLT_RATIFY, Z2_OUTREACH_RATIFY)
are surfaced as outputs, never executed autonomously.

Three built-in pipelines:
  SESSION_CLOSE_PIPELINE   — runs on every session close
  REPO_ANALYSIS_PIPELINE   — runs when a new external repo is analyzed
  DOCUMENT_SCORE_PIPELINE  — runs when any document enters the system

Usage:
    python haios_pipeline_v1_0.py --pipeline SESSION_CLOSE --input <json>
    python haios_pipeline_v1_0.py --pipeline REPO_ANALYSIS --input <json>
    python haios_pipeline_v1_0.py --pipeline DOCUMENT_SCORE --input <json>
    python haios_pipeline_v1_0.py --pipeline CUSTOM --stages <json> --input <json>
    python haios_pipeline_v1_0.py --smoke-test
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

TOOL_NAME = "haios_pipeline"
TOOL_VERSION = "1.0.0"
SESSION_ID = "S-052026-01"

# ---------------------------------------------------------------------------
# Failure behaviour enum
# ---------------------------------------------------------------------------

class OnFailure(str, Enum):
    STOP    = "STOP"    # hard failure — halt pipeline, notify immediately
    WARN    = "WARN"    # soft failure — log and continue
    CONTINUE = "CONTINUE"  # informational — never blocks


# ---------------------------------------------------------------------------
# Stage dataclass
# ---------------------------------------------------------------------------

@dataclass
class PipelineStage:
    """One stage in a pipeline.

    tool_name       : importable module name OR path to .py file
    input_map       : dict mapping stage input keys to upstream output keys
                      e.g. {"text": "document_analyzer.density_scores"}
                      Use "__initial__" prefix to reference initial_input keys.
    output_fields   : list of top-level keys to extract and pass forward
    on_failure      : STOP | WARN | CONTINUE
    description     : human-readable label (appears in report and Slack)
    timeout_seconds : max seconds to wait for subprocess (0 = no limit)
    """
    tool_name: str
    input_map: Dict[str, str] = field(default_factory=dict)
    output_fields: List[str] = field(default_factory=list)
    on_failure: OnFailure = OnFailure.STOP
    description: str = ""
    timeout_seconds: int = 120


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    stage_index: int
    tool_name: str
    description: str
    status: str          # PASS | WARN | FAIL | SKIP
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class PipelineResult:
    pipeline_name: str
    session_id: str
    timestamp: str
    overall_status: str   # PASS | WARN | FAIL
    stage_results: List[StageResult] = field(default_factory=list)
    accumulated_outputs: Dict[str, Any] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)
    z2_required: bool = False
    z2_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["stage_results"] = [asdict(r) for r in self.stage_results]
        return d


# ---------------------------------------------------------------------------
# Built-in pipeline definitions
# ---------------------------------------------------------------------------

SESSION_CLOSE_PIPELINE: List[PipelineStage] = [
    PipelineStage(
        tool_name="acat_protocol_auditor_v1_1",
        input_map={"close_post": "__initial__.close_post"},
        output_fields=["overall_verdict", "hard_failures", "soft_failures",
                        "resonance_score"],
        on_failure=OnFailure.STOP,
        description="Protocol audit — Section B compliance check",
    ),
    PipelineStage(
        tool_name="corpus_integrity_validator_v1_1",
        input_map={"corpus_path": "__initial__.corpus_path"},
        output_fields=["result", "violations", "n_total", "n_phase1", "n_li"],
        on_failure=OnFailure.STOP,
        description="Corpus integrity — N counts, schema, no duplicates",
    ),
    PipelineStage(
        tool_name="drift_catalog_validator_v1_1",
        input_map={"drift_entries": "__initial__.drift_entries"},
        output_fields=["result", "new_signals", "unresolved_signals"],
        on_failure=OnFailure.WARN,
        description="Drift catalog — named signals properly formatted",
    ),
    PipelineStage(
        tool_name="haios_report_writer_v1_0",
        input_map={
            "pipeline_name": "__pipeline__.name",
            "stage_results": "__pipeline__.stage_results",
            "session_id": "__initial__.session_id",
        },
        output_fields=["report_text", "report_path"],
        on_failure=OnFailure.WARN,
        description="Report writer — human-readable session close summary",
    ),
    PipelineStage(
        tool_name="haios_notify_dispatcher_v1_0",
        input_map={
            "report_text": "haios_report_writer_v1_0.report_text",
            "channel": "__initial__.notify_channel",
            "session_id": "__initial__.session_id",
        },
        output_fields=["dispatched", "dispatch_log"],
        on_failure=OnFailure.WARN,
        description="Notify — post summary to #acat-monitor",
    ),
]

REPO_ANALYSIS_PIPELINE: List[PipelineStage] = [
    PipelineStage(
        tool_name="acat_repo_analyzer",
        input_map={"repo_url": "__initial__.repo_url"},
        output_fields=["signals", "recommended_issue_focus",
                        "analysis_source", "issue_body_draft"],
        on_failure=OnFailure.STOP,
        description="Repo analyzer — ACAT-framed signal scan",
    ),
    PipelineStage(
        tool_name="acat_document_analyzer_v1_1",
        input_map={"input": "acat_repo_analyzer.issue_body_draft",
                   "name": "__initial__.repo_url"},
        output_fields=["truth", "service", "harm", "humility", "handoff",
                        "scheme", "syc"],
        on_failure=OnFailure.WARN,
        description="Document analyzer — score the generated issue draft",
    ),
    PipelineStage(
        tool_name="haios_report_writer_v1_0",
        input_map={
            "pipeline_name": "__pipeline__.name",
            "stage_results": "__pipeline__.stage_results",
            "session_id": "__initial__.session_id",
        },
        output_fields=["report_text", "report_path"],
        on_failure=OnFailure.WARN,
        description="Report writer — repo analysis summary for Night review",
    ),
    PipelineStage(
        tool_name="haios_notify_dispatcher_v1_0",
        input_map={
            "report_text": "haios_report_writer_v1_0.report_text",
            "channel": "__initial__.notify_channel",
            "session_id": "__initial__.session_id",
            "z2_queue_item": "__pipeline__.z2_required",
        },
        output_fields=["dispatched", "dispatch_log"],
        on_failure=OnFailure.WARN,
        description="Notify — post to #acat-monitor, queue Z2 outreach decision",
    ),
]

DOCUMENT_SCORE_PIPELINE: List[PipelineStage] = [
    PipelineStage(
        tool_name="acat_document_analyzer_v1_1",
        input_map={"input": "__initial__.document_path",
                   "name": "__initial__.document_name",
                   "session": "__initial__.session_id"},
        output_fields=["truth", "service", "harm", "autonomy", "value",
                        "humility", "scheme", "power", "syc", "consist",
                        "fair", "handoff"],
        on_failure=OnFailure.STOP,
        description="Document analyzer — 12-dimension density score",
    ),
    PipelineStage(
        tool_name="haios_report_writer_v1_0",
        input_map={
            "pipeline_name": "__pipeline__.name",
            "stage_results": "__pipeline__.stage_results",
            "session_id": "__initial__.session_id",
            "document_name": "__initial__.document_name",
        },
        output_fields=["report_text", "report_path"],
        on_failure=OnFailure.WARN,
        description="Report writer — document score summary",
    ),
    PipelineStage(
        tool_name="haios_notify_dispatcher_v1_0",
        input_map={
            "report_text": "haios_report_writer_v1_0.report_text",
            "channel": "__initial__.notify_channel",
            "session_id": "__initial__.session_id",
        },
        output_fields=["dispatched", "dispatch_log"],
        on_failure=OnFailure.WARN,
        description="Notify — post document score to #acat-monitor",
    ),
]

PIPELINE_REGISTRY = {
    "SESSION_CLOSE":    SESSION_CLOSE_PIPELINE,
    "REPO_ANALYSIS":    REPO_ANALYSIS_PIPELINE,
    "DOCUMENT_SCORE":   DOCUMENT_SCORE_PIPELINE,
}


# ---------------------------------------------------------------------------
# Input resolution
# ---------------------------------------------------------------------------

def resolve_input(
    input_map: Dict[str, str],
    initial_input: Dict[str, Any],
    accumulated: Dict[str, Any],
    pipeline_meta: Dict[str, Any],
) -> Dict[str, Any]:
    """Resolve stage inputs from initial input, accumulated outputs, and
    pipeline metadata using the dot-notation input_map.

    Prefixes:
      __initial__.key          → initial_input["key"]
      __pipeline__.key         → pipeline_meta["key"]
      tool_name.output_key     → accumulated["tool_name"]["output_key"]
    """
    resolved = {}
    for dest_key, source_path in input_map.items():
        if source_path.startswith("__initial__."):
            src_key = source_path[len("__initial__."):]
            resolved[dest_key] = initial_input.get(src_key)
        elif source_path.startswith("__pipeline__."):
            src_key = source_path[len("__pipeline__."):]
            resolved[dest_key] = pipeline_meta.get(src_key)
        else:
            parts = source_path.split(".", 1)
            if len(parts) == 2:
                tool, key = parts
                tool_out = accumulated.get(tool, {})
                resolved[dest_key] = tool_out.get(key)
            else:
                resolved[dest_key] = accumulated.get(source_path)
    return resolved


# ---------------------------------------------------------------------------
# Stage executor
# ---------------------------------------------------------------------------

def execute_stage(
    stage: PipelineStage,
    stage_input: Dict[str, Any],
    stage_index: int,
) -> StageResult:
    """Execute one pipeline stage.

    Strategy: attempt to import the tool as a module and call run(input_dict).
    Fall back to subprocess if import fails (handles .py file paths and
    tools not on sys.path). If both fail, record error per on_failure policy.
    """
    start_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    def elapsed() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000) - start_ms

    # --- attempt module import ---
    try:
        import importlib
        mod_name = stage.tool_name.replace("-", "_")
        mod = importlib.import_module(mod_name)
        if hasattr(mod, "run"):
            raw_output = mod.run(stage_input)
            output = raw_output if isinstance(raw_output, dict) else {"result": raw_output}
            status = "FAIL" if output.get("result") == "FAIL" else "PASS"
            if output.get("warnings"):
                status = "WARN"
            return StageResult(
                stage_index=stage_index,
                tool_name=stage.tool_name,
                description=stage.description,
                status=status,
                output=output,
                duration_ms=elapsed(),
            )
    except (ImportError, ModuleNotFoundError):
        pass  # fall through to subprocess
    except Exception as exc:
        return StageResult(
            stage_index=stage_index,
            tool_name=stage.tool_name,
            description=stage.description,
            status="FAIL",
            error=f"Module execution error: {exc}",
            duration_ms=elapsed(),
        )

    # --- attempt subprocess ---
    tool_path = Path(stage.tool_name)
    if not tool_path.exists():
        # try common locations
        for candidate in [
            Path(__file__).parent / f"{stage.tool_name}.py",
            Path(__file__).parent / f"{stage.tool_name}",
        ]:
            if candidate.exists():
                tool_path = candidate
                break

    if tool_path.exists():
        try:
            cmd = [sys.executable, str(tool_path), "--input", json.dumps(stage_input)]
            timeout = stage.timeout_seconds if stage.timeout_seconds > 0 else None
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if proc.returncode == 0:
                try:
                    output = json.loads(proc.stdout.strip())
                except json.JSONDecodeError:
                    output = {"raw_output": proc.stdout.strip()}
                return StageResult(
                    stage_index=stage_index,
                    tool_name=stage.tool_name,
                    description=stage.description,
                    status="PASS",
                    output=output,
                    duration_ms=elapsed(),
                )
            else:
                return StageResult(
                    stage_index=stage_index,
                    tool_name=stage.tool_name,
                    description=stage.description,
                    status="FAIL",
                    error=proc.stderr.strip() or f"Return code {proc.returncode}",
                    duration_ms=elapsed(),
                )
        except subprocess.TimeoutExpired:
            return StageResult(
                stage_index=stage_index,
                tool_name=stage.tool_name,
                description=stage.description,
                status="FAIL",
                error=f"Timeout after {stage.timeout_seconds}s",
                duration_ms=elapsed(),
            )
        except Exception as exc:
            return StageResult(
                stage_index=stage_index,
                tool_name=stage.tool_name,
                description=stage.description,
                status="FAIL",
                error=f"Subprocess error: {exc}",
                duration_ms=elapsed(),
            )

    # --- tool not found ---
    return StageResult(
        stage_index=stage_index,
        tool_name=stage.tool_name,
        description=stage.description,
        status="FAIL",
        error=f"Tool not found: {stage.tool_name}",
        duration_ms=elapsed(),
    )


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline(
    stages: List[PipelineStage],
    initial_input: Dict[str, Any],
    pipeline_name: str = "CUSTOM",
) -> PipelineResult:
    """Execute a pipeline: resolve inputs, run stages in sequence,
    accumulate outputs, handle failures per on_failure policy.

    Returns a PipelineResult with per-stage outcomes and accumulated outputs.
    Never raises — errors are captured in the result.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    result = PipelineResult(
        pipeline_name=pipeline_name,
        session_id=initial_input.get("session_id", "UNKNOWN"),
        timestamp=timestamp,
        overall_status="PASS",
    )

    accumulated: Dict[str, Any] = {}
    hard_stopped = False

    for idx, stage in enumerate(stages):
        if hard_stopped:
            result.stage_results.append(StageResult(
                stage_index=idx,
                tool_name=stage.tool_name,
                description=stage.description,
                status="SKIP",
                error="Pipeline halted by prior STOP failure",
            ))
            continue

        # Build pipeline metadata for __pipeline__ references
        pipeline_meta = {
            "name": pipeline_name,
            "stage_results": [asdict(r) for r in result.stage_results],
            "accumulated": accumulated,
        }

        # Resolve inputs
        stage_input = resolve_input(
            stage.input_map, initial_input, accumulated, pipeline_meta
        )

        # Execute
        stage_result = execute_stage(stage, stage_input, idx)
        result.stage_results.append(stage_result)

        # Accumulate outputs
        if stage_result.status in ("PASS", "WARN") and stage_result.output:
            extracted = {
                k: v for k, v in stage_result.output.items()
                if not stage.output_fields or k in stage.output_fields
            }
            accumulated[stage.tool_name] = extracted
            result.accumulated_outputs.update(extracted)

        # Handle failure
        if stage_result.status == "FAIL":
            msg = (f"Stage {idx} [{stage.tool_name}] FAILED: "
                   f"{stage_result.error}")
            result.error_log.append(msg)

            if stage.on_failure == OnFailure.STOP:
                hard_stopped = True
                result.overall_status = "FAIL"
                result.z2_required = True
                result.z2_reason = (
                    f"Hard failure at stage {idx} ({stage.description}). "
                    "Human review required before pipeline can resume."
                )
            elif stage.on_failure == OnFailure.WARN:
                if result.overall_status == "PASS":
                    result.overall_status = "WARN"
            # CONTINUE: no status change

        elif stage_result.status == "WARN":
            if result.overall_status == "PASS":
                result.overall_status = "WARN"

    # Z2 check: any stage that produced z2_required signal
    for sr in result.stage_results:
        if sr.output.get("z2_required"):
            result.z2_required = True
            result.z2_reason = sr.output.get(
                "z2_reason", f"Stage {sr.stage_index} requests Z2 review"
            )

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"HAIOS Pipeline Coordinator {TOOL_VERSION}"
    )
    parser.add_argument(
        "--pipeline", "-p",
        choices=list(PIPELINE_REGISTRY.keys()) + ["CUSTOM"],
        default="CUSTOM",
        help="Named pipeline to run, or CUSTOM to provide --stages",
    )
    parser.add_argument(
        "--stages", "-s",
        help="JSON array of stage definitions (CUSTOM mode only)",
    )
    parser.add_argument(
        "--input", "-i",
        required=False,
        help="JSON dict of initial inputs",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Path to write JSON result (default: stdout)",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run built-in smoke test and exit",
    )
    args = parser.parse_args()

    if args.smoke_test:
        passed = run_smoke_test()
        sys.exit(0 if passed else 1)

    # Load pipeline
    if args.pipeline == "CUSTOM":
        if not args.stages:
            print("ERROR: --stages required for CUSTOM pipeline", file=sys.stderr)
            sys.exit(1)
        raw_stages = json.loads(args.stages)
        stages = [
            PipelineStage(
                tool_name=s["tool_name"],
                input_map=s.get("input_map", {}),
                output_fields=s.get("output_fields", []),
                on_failure=OnFailure(s.get("on_failure", "STOP")),
                description=s.get("description", ""),
                timeout_seconds=s.get("timeout_seconds", 120),
            )
            for s in raw_stages
        ]
        pipeline_name = "CUSTOM"
    else:
        stages = PIPELINE_REGISTRY[args.pipeline]
        pipeline_name = args.pipeline

    # Load initial input
    initial_input: Dict[str, Any] = {}
    if args.input:
        initial_input = json.loads(args.input)

    # Run
    result = run_pipeline(stages, initial_input, pipeline_name)
    result_dict = result.to_dict()

    # Output
    output_json = json.dumps(result_dict, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"[{result.overall_status}] Pipeline {pipeline_name} → {args.output}",
              file=sys.stderr)
    else:
        print(output_json)

    sys.exit(0 if result.overall_status in ("PASS", "WARN") else 1)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> bool:
    """Builder v1.7 compliant smoke test.
    Positive: single-stage WARN pipeline completes with WARN status.
    Negative: STOP failure halts pipeline and skips downstream stages.
    """
    print(f"[SMOKE] {TOOL_NAME} v{TOOL_VERSION}")

    # Positive: WARN stage completes, downstream CONTINUE stage runs
    warn_stage = PipelineStage(
        tool_name="__smoke_nonexistent_warn__",
        on_failure=OnFailure.WARN,
        description="Smoke warn stage",
    )
    continue_stage = PipelineStage(
        tool_name="__smoke_nonexistent_continue__",
        on_failure=OnFailure.CONTINUE,
        description="Smoke continue stage",
    )
    result = run_pipeline([warn_stage, continue_stage], {}, "SMOKE_WARN")
    assert result.overall_status == "WARN", (
        f"Expected WARN, got {result.overall_status}"
    )
    assert len(result.stage_results) == 2, (
        f"Expected 2 stages, got {len(result.stage_results)}"
    )
    assert result.stage_results[0].status == "FAIL"   # tool not found → FAIL
    assert result.stage_results[1].status == "FAIL"   # same, but CONTINUE

    # Negative: STOP failure halts pipeline
    stop_stage = PipelineStage(
        tool_name="__smoke_nonexistent_stop__",
        on_failure=OnFailure.STOP,
        description="Smoke stop stage",
    )
    downstream = PipelineStage(
        tool_name="__smoke_should_skip__",
        on_failure=OnFailure.CONTINUE,
        description="Should be SKIP",
    )
    result2 = run_pipeline([stop_stage, downstream], {}, "SMOKE_STOP")
    assert result2.overall_status == "FAIL", (
        f"Expected FAIL, got {result2.overall_status}"
    )
    assert result2.stage_results[1].status == "SKIP", (
        f"Expected SKIP, got {result2.stage_results[1].status}"
    )
    assert result2.z2_required is True

    # Input resolution smoke
    initial = {"doc_path": "/tmp/test.txt", "session_id": "S-TEST"}
    stage_with_map = PipelineStage(
        tool_name="__smoke_map__",
        input_map={"path": "__initial__.doc_path"},
        on_failure=OnFailure.CONTINUE,
    )
    result3 = run_pipeline([stage_with_map], initial, "SMOKE_MAP")
    assert result3.session_id == "S-TEST"

    print("[SMOKE] All assertions passed.")
    return True


if __name__ == "__main__":
    main()
