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

    explicit_handles = bool(handles)

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

        # GET /hackers/programs already returns full program resources. Reuse
        # those observations for account-wide portfolio scans. Explicit --handle
        # scans resolve the requested program from that same authenticated list,
        # avoiding reliance on a separate detail response shape.
        if explicit_handles:
            try:
                program = client.find_program(handle, page_size=page_size)
            except Exception as exc:
                snapshot.programs.append(
                    PortfolioProgramObservation(
                        handle=handle,
                        state="OBSERVATION_FAILED",
                        error_type=type(exc).__name__,
                        error_detail=f"stage=find_program; {str(exc)[:210]}",
                    )
                )
                continue
        else:
            program = seed

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

        # Exclusions are authorization-stage evidence. Portfolio ranking does not
        # require them, so defer this request rather than making it a fatal
        # dependency for initial scope hydration.
        graph = build_scope_graph(
            program,
            scopes,
            [],
            observed_at=observed_at,
            exclusions_state="DEFERRED_FOR_POLICY_REVIEW",
        )
        snapshot.programs.append(
            PortfolioProgramObservation(
                handle=handle,
                state="OBSERVED",
                graph=graph,
            )
        )

    snapshot.programs.sort(key=lambda row: row.handle.casefold())
    return snapshot
