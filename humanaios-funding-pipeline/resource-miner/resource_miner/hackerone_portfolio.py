from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .normalize import utcnow_iso
from .security_scope import ProgramScopeGraph, build_scope_graph


@dataclass
class PortfolioProgramObservation:
    handle: str
    state: str
    graph: ProgramScopeGraph | None = None
    error_type: str | None = None
    error_detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.graph is not None:
            data["graph"] = self.graph.to_dict()
        return data


@dataclass
class HackerOnePortfolioSnapshot:
    schema: str = "humanaios.hackerone-portfolio.v1"
    observed_at: str = ""
    source: str = "HackerOne Hacker API"
    programs: list[PortfolioProgramObservation] = field(default_factory=list)
    authority_effect: str = "NONE"
    execution_capability: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "observed_at": self.observed_at,
            "source": self.source,
            "programs": [program.to_dict() for program in self.programs],
            "authority_effect": self.authority_effect,
            "execution_capability": self.execution_capability,
        }


def _handle(program: dict[str, Any]) -> str:
    attrs = program.get("attributes") or {}
    return str(attrs.get("handle") or "").strip()


def scan_portfolio(
    client: Any,
    *,
    handles: list[str] | None = None,
    page_size: int = 100,
    max_programs: int | None = None,
) -> HackerOnePortfolioSnapshot:
    """Hydrate HackerOne metadata only. No program asset is contacted."""
    observed_at = utcnow_iso()
    if handles:
        seeds = [{"attributes": {"handle": handle}} for handle in handles]
    else:
        seeds = client.list_programs(page_size=page_size)

    if max_programs is not None:
        max_programs = max(0, int(max_programs))
        seeds = list(seeds)[:max_programs]

    snapshot = HackerOnePortfolioSnapshot(observed_at=observed_at)

    for seed in seeds:
        handle = _handle(seed)
        if not handle:
            snapshot.programs.append(
                PortfolioProgramObservation(
                    handle="",
                    state="INVALID_PROGRAM_METADATA",
                    error_type="ValueError",
                    error_detail="program object missing handle",
                )
            )
            continue
        try:
            program = client.get_program(handle)
        except Exception as exc:
            snapshot.programs.append(
                PortfolioProgramObservation(
                    handle=handle,
                    state="OBSERVATION_FAILED",
                    error_type=type(exc).__name__,
                    error_detail=f"stage=get_program; {str(exc)[:210]}",
                )
            )
            continue

        try:
            scopes = client.get_structured_scopes(handle, page_size=page_size)
        except Exception as exc:
            snapshot.programs.append(
                PortfolioProgramObservation(
                    handle=handle,
                    state="OBSERVATION_FAILED",
                    error_type=type(exc).__name__,
                    error_detail=f"stage=structured_scopes; {str(exc)[:200]}",
                )
            )
            continue

        try:
            exclusions = client.get_scope_exclusions(handle)
        except Exception as exc:
            snapshot.programs.append(
                PortfolioProgramObservation(
                    handle=handle,
                    state="OBSERVATION_FAILED",
                    error_type=type(exc).__name__,
                    error_detail=f"stage=scope_exclusions; {str(exc)[:200]}",
                )
            )
            continue

        graph = build_scope_graph(program, scopes, exclusions, observed_at=observed_at)
        snapshot.programs.append(
            PortfolioProgramObservation(
                handle=handle,
                state="OBSERVED",
                graph=graph,
            )
        )

    snapshot.programs.sort(key=lambda row: row.handle.casefold())
    return snapshot
