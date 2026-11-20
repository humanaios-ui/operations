"""Read-only window onto a research data directory. There is no write path."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .protocol import ToolError

ALLOWED = {".json", ".jsonl", ".csv", ".md", ".txt", ".yaml", ".yml"}
MAX_READ = 64 * 1024


class Datasets:
    def __init__(self, root: Path | None):
        self.root = root.resolve() if root else None

    def _need(self) -> Path:
        if not self.root or not self.root.is_dir():
            raise ToolError("no dataset root configured (set HUB_DATASET_ROOT)")
        return self.root

    def list(self, limit: int = 200) -> list[dict[str, Any]]:
        root = self._need()
        out = []
        for p in sorted(root.rglob("*")):
            if p.is_symlink() or not p.is_file() or p.suffix.lower() not in ALLOWED:
                continue
            out.append({"name": p.relative_to(root).as_posix(), "bytes": p.stat().st_size})
            if len(out) >= limit:
                break
        return out

    def read(self, name: str, offset: int = 0, length: int = MAX_READ) -> dict[str, Any]:
        root = self._need()
        target = (root / name)
        if target.is_symlink() or not target.exists():
            raise ToolError("dataset not found")
        real = target.resolve()
        if root not in real.parents or not real.is_file() or real.suffix.lower() not in ALLOWED:
            raise ToolError("dataset not found")
        length = max(1, min(length, MAX_READ))
        with real.open("rb") as fh:
            fh.seek(offset)
            chunk = fh.read(length)
        return {"name": name, "offset": offset, "bytes": len(chunk),
                "total_bytes": real.stat().st_size, "text": chunk.decode("utf-8", "replace"),
                "read_only": True}
