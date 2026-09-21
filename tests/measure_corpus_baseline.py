#!/usr/bin/env python3
"""Baseline corpus measurement for P34-X Phase 1.

Measures precision/recall/F1 on seeded CONTAM and CLEAN examples.
Entry gate: ≥0.85 baseline precision before Phase 2.
"""

import json
from pathlib import Path
from p34x_temporal_extractor import TemporalExtractor, ExtractorConfig
from p34x_temporal_extractor.findings import Severity
from p34x_temporal_extractor.evidence import LedgerProvider


def load_jsonl(filepath):
    """Load JSONL corpus file."""
    examples = []
    if Path(filepath).exists():
        with open(filepath) as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))
    return examples


def measure_baseline():
    """Measure precision/recall against seeded corpus."""

    # Initialize extractor
    config = ExtractorConfig(
        evidence_providers=[LedgerProvider()],
    )
    extractor = TemporalExtractor(config)

    # Load corpus
    contam_examples = load_jsonl("tests/corpus/contam.jsonl")
    clean_examples = load_jsonl("tests/corpus/clean.jsonl")

    print(f"Loaded {len(contam_examples)} CONTAM examples")
    print(f"Loaded {len(clean_examples)} CLEAN examples")
    print()

    # Measure CONTAM detection (recall)
    contam_detected = 0
    contam_missed = []

    for ex in contam_examples:
        text = ex["text"]
        expected_category = ex.get("category")
        result = extractor.extract(text)

        if len(result.findings) > 0:
            contam_detected += 1
        else:
            contam_missed.append((text, expected_category))

    contam_recall = contam_detected / len(contam_examples) if contam_examples else 0

    print(f"CONTAM Detection Rate (Recall): {contam_recall:.2%} ({contam_detected}/{len(contam_examples)})")
    if contam_missed:
        print(f"  Missed CONTAM examples:")
        for text, cat in contam_missed[:5]:
            print(f"    - {text[:60]}")
    print()

    # Measure CLEAN false positives (precision)
    clean_errors = 0
    clean_errors_list = []

    for ex in clean_examples:
        text = ex["text"]
        should_pass = ex.get("should_pass", True)
        result = extractor.extract(text)

        errors = [f for f in result.findings if f.severity == Severity.ERROR]
        if should_pass and errors:
            clean_errors += 1
            clean_errors_list.append((text, errors[0].text))

    clean_precision = 1.0 - (clean_errors / len(clean_examples) if clean_examples else 0)

    print(f"CLEAN Precision (No false positives): {clean_precision:.2%} ({len(clean_examples) - clean_errors}/{len(clean_examples)})")
    if clean_errors_list:
        print(f"  False positives:")
        for text, finding_text in clean_errors_list[:5]:
            print(f"    - Text: {text[:60]}")
            print(f"      Finding: {finding_text[:40]}")
    print()

    # Compute F1
    if contam_detected + clean_errors > 0:
        # True positives: contam_detected
        # False positives: clean_errors
        # False negatives: contam_missed
        precision = contam_detected / (contam_detected + clean_errors) if (contam_detected + clean_errors) > 0 else 0
        recall = contam_recall
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        print(f"Aggregated Metrics:")
        print(f"  Precision: {precision:.2%}")
        print(f"  Recall: {recall:.2%}")
        print(f"  F1-Score: {f1:.2%}")
        print()

        # Entry gate check
        if precision >= 0.85:
            print("✅ Entry gate PASSED: ≥0.85 baseline precision")
        else:
            print(f"❌ Entry gate FAILED: {precision:.2%} < 0.85 required")

    return {
        "contam_recall": contam_recall,
        "clean_precision": clean_precision,
        "samples_contam": len(contam_examples),
        "samples_clean": len(clean_examples),
    }


if __name__ == "__main__":
    measure_baseline()
