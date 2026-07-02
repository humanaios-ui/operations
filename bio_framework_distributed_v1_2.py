"""
bio_framework_distributed_v1_2.py  (B2 — organ coverage)

Two shapes the Phase-3 mapping flagged as having NO clean single-owner model:

  * DistributedFunction — a Western unified system with no single Eastern owner;
    responsibility is SHARED/BROADCAST across multiple Zang (mapping §5, §8.2).
    Implemented for the nervous system = Wu Shen (Five Spirits): Shen-Heart,
    Hun-Liver, Po-Lung, Yi-Spleen, Zhi-Kidney. No coordinating node except
    Heart loosely "emperor" (weighted heavier in coherence).

  * SanJiaoCoordinator — the San Jiao (Triple Burner): a full orphan, no Zang
    pair, no anatomical correlate. Three body-cavity zones governing overall
    fluid (Jinye) passage. Modelled as a cross-zone coordinator, not an organ.

Extension over core v1.2 — no core changes. Facet vitality is read from the
EXISTING resource layer, so each Zang keeps single ownership of its resource
while contributing a facet to the distributed function (the whole point).
The Six Fu (bowels) are NOT re-invented here: they follow their paired Zang,
which is the already-solved 'paired component' pattern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from bio_framework_core_v1_2 import Element, ResourcePool, Signal, OrganComponent


# --- Wu Shen: each Zang houses a spirit whose vitality reads an existing resource ---
FACET_SUBSTRATE: Dict[Element, tuple[str, Callable[[ResourcePool], float]]] = {
    Element.FIRE:  ("Shen", lambda r: r.shen),                    # Heart — consciousness
    Element.WOOD:  ("Hun",  lambda r: r.blood),                   # Liver — ethereal/emotional (blood)
    Element.METAL: ("Po",   lambda r: r.qi_of(Element.METAL)),    # Lung  — corporeal/reflexive
    Element.EARTH: ("Yi",   lambda r: r.qi_of(Element.EARTH)),    # Spleen— thought/intellect
    Element.WATER: ("Zhi",  lambda r: r.jinye),                   # Kidney— willpower (jing proxy)
}


@dataclass
class DistributedFunction:
    """A Western unified system with no single Eastern owner. Its behaviour is
    ASSEMBLED from facets each participating Zang holds; a signal to it is
    BROADCAST to every facet-holder (pub/sub), not routed to one node."""
    name: str
    facets: Dict[Element, tuple[str, Callable[[ResourcePool], float]]]
    coordinator: Element                     # loosely-in-charge node (Heart)
    coordinator_weight: float = 2.0

    def assemble(self, resources: ResourcePool) -> dict:
        vitality = {spirit: reader(resources)
                    for (spirit, reader) in self.facets.values()}
        # weighted coherence — coordinator heavier ("Heart as emperor")
        wsum, w = 0.0, 0.0
        for e, (spirit, reader) in self.facets.items():
            weight = self.coordinator_weight if e is self.coordinator else 1.0
            wsum += reader(resources) * weight
            w += weight
        coherence = round(wsum / w, 2) if w else 0.0
        weakest = min(vitality, key=vitality.get) if vitality else None
        return {"system": self.name, "facets": vitality,
                "coherence": coherence, "weakest_facet": weakest}

    def broadcast(self, components: Dict[Element, OrganComponent],
                  resources: ResourcePool, signal: Signal) -> None:
        """A system-level signal reaches ALL facet-holders (distributed)."""
        for e in self.facets:
            if e in components:
                components[e].receive_signal(resources, signal)


WuShen = DistributedFunction(
    name="NervousSystem(WuShen)", facets=FACET_SUBSTRATE, coordinator=Element.FIRE
)


# --- San Jiao: the full orphan — a cross-zone fluid-passage coordinator ---
@dataclass
class SanJiaoCoordinator:
    """Triple Burner. No Zang pair, no anatomical correlate. Governs Jinye
    passage across three body-cavity zones. A coordinator over shared fluid
    state, not an organ that owns a resource."""
    STAGNATION_THRESHOLD: float = 25.0
    zones: List[str] = field(default_factory=lambda: ["upper", "middle", "lower"])

    def fluid_passage(self, resources: ResourcePool) -> dict:
        jinye = resources.jinye
        status = "stagnant" if jinye < self.STAGNATION_THRESHOLD else "flowing"
        # even distribution across zones is the healthy case; report per-zone share
        if not self.zones:
            raise ValueError("SanJiaoCoordinator.zones must not be empty")
        share = round(jinye / len(self.zones), 2)
        return {"jinye": jinye, "status": status,
                "per_zone": {z: share for z in self.zones}}

    def fail_mode(self, resources: ResourcePool) -> str | None:
        if resources.jinye < self.STAGNATION_THRESHOLD:
            return "San Jiao fluid stagnation (Jinye passage impaired)"
        return None


SanJiao = SanJiaoCoordinator()
