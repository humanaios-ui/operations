"""Hashes of the code that produces and scores evidence. Pinned in the frozen plan (KD-2)."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "writer_sha256": ROOT / "src" / "writer.py",
    "bridge_sha256": ROOT / "integration" / "bridge_v2.py",
    "scorer_sha256": ROOT / "integration" / "scoring.py",
    "oracle_sha256": ROOT / "integration" / "oracle.py",
    "readback_sha256": ROOT / "integration" / "readback.py",
    "service_sha256": ROOT / "src" / "service.py",
    "verifier_sha256": ROOT / "src" / "verifier.py",
    "pins_sha256": ROOT / "src" / "pins.py",
    "responses_sha256": ROOT / "src" / "responses.py",
}


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_pins():
    return {name: file_sha256(path) for name, path in FILES.items()}
