"""
bio_framework_core_v1_2.py

Phase 4 translation of BIO_SYSTEMS_MAPPING_V1.md into a programming framework.
v1.1: qi decomposed from a single global scalar into per-Element allocations.
Blood/Jinye/Shen remain global scalars for now (out of scope for this pass;
same treatment likely needed later, see stress-test note at bottom).

Five code shapes, one per Phase 3 finding:
  1. OrganComponent          -> clean 1:1 matches (Heart, Lung)
  2. CompositeOrganComponent -> Eastern node spanning multiple Western modules (Kidney, Spleen)
  3. CrossCuttingRegulator   -> middleware, not a component (Liver-Qi, Wei Qi)
  4. ChannelGraph            -> Jing-Luo meridian network; a topology, not a node
  5. ResourcePool            -> Qi (per-Element) / Jinye / Blood / Shen as shared state
  + WuXingEngine             -> Five Element generative/control cycles now MOVE qi
                                 between specific elements instead of touching a
                                 shared scalar every organ happened to read.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Element(Enum):
    WOOD = "Liver"
    FIRE = "Heart"
    EARTH = "Spleen"
    METAL = "Lung"
    WATER = "Kidney"

GENERATIVE_CYCLE = {
    Element.WOOD: Element.FIRE,
    Element.FIRE: Element.EARTH,
    Element.EARTH: Element.METAL,
    Element.METAL: Element.WATER,
    Element.WATER: Element.WOOD,
}

CONTROL_CYCLE = {
    Element.WOOD: Element.EARTH,
    Element.EARTH: Element.WATER,
    Element.WATER: Element.FIRE,
    Element.FIRE: Element.METAL,
    Element.METAL: Element.WOOD,
}


# ---------------------------------------------------------------------------
# v1.2 — Signal semantics (B1). A received signal now carries its KIND, so a
# component can respond to *why* it was reached, not just *that* it was.
#
#   GENERATIVE — Sheng cycle: the mother element nourishes this one (Wood->Fire).
#   CONTROL    — Ke cycle: the controller restrains this one (Wood->Earth).
#   CHANNEL    — Jing-Luo meridian: a named connectivity edge fired.
#
# Separation of concerns (avoids double-counting): the WuXingEngine already
# moves *qi* (the resource economy). receive_signal is the organ's FUNCTIONAL
# response to being signalled — it acts on non-qi resources (shen/blood/jinye)
# or on its own fail-state, NOT on qi again.
# ---------------------------------------------------------------------------

class SignalKind(Enum):
    GENERATIVE = "generative"
    CONTROL = "control"
    CHANNEL = "channel"


@dataclass
class Signal:
    kind: SignalKind
    source: str
    strength: float = 1.0


# ---------------------------------------------------------------------------
# 1. Resource layer — qi is now per-Element. Blood/Jinye/Shen stay global
#    scalars this pass (they didn't cause the collateral-damage bug the
#    stress test surfaced, so they weren't in scope for this fix).
# ---------------------------------------------------------------------------

@dataclass
class ResourcePool:
    qi_by_element: Dict[Element, float] = field(
        default_factory=lambda: {e: 100.0 for e in Element}
    )
    blood: float = 100.0
    blood_contributions: Dict[str, float] = field(default_factory=dict)
    jinye: float = 100.0
    shen: float = 100.0

    def contribute_blood(self, source: str, amount: float) -> None:
        """Organ-attributed blood contribution. Records the source alongside
        applying the delta, so a contributor's dropout is independently
        visible instead of hiding inside an anonymous shared scalar. Use for
        organ regen; use adjust(blood=...) for external, non-organ-owned
        events (injury, chronic loss) that no single component is
        responsible for."""
        self.blood_contributions[source] = amount
        self.blood = max(0.0, min(100.0, self.blood + amount))

    def qi_of(self, element: Element) -> float:
        return self.qi_by_element[element]

    def adjust_qi(self, element: Element, delta: float) -> None:
        self.qi_by_element[element] = max(
            0.0, min(100.0, self.qi_by_element[element] + delta)
        )

    @property
    def total_qi(self) -> float:
        """Systemic average across all five elements — reporting only,
        never used for gating logic (that was the old bug)."""
        return sum(self.qi_by_element.values()) / len(self.qi_by_element)

    def adjust(self, **deltas: float) -> None:
        for k, v in deltas.items():
            if k == "qi":
                raise ValueError(
                    "qi is per-Element now — use adjust_qi(element, delta) instead"
                )
            setattr(self, k, max(0.0, min(100.0, getattr(self, k) + v)))


# ---------------------------------------------------------------------------
# 2. Base interface — every component now declares its home Element so the
#    resource layer and Wu Xing engine know which allocation belongs to it.
# ---------------------------------------------------------------------------

class OrganComponent(ABC):
    name: str
    element: Element

    @abstractmethod
    def function(self, resources: ResourcePool, inputs: dict) -> dict: ...

    @abstractmethod
    def regulate(self, resources: ResourcePool) -> None:
        """Autonomous per-tick baseline function. Called exactly once per
        tick, by the tick loop only. Never call this from ChannelGraph or
        WuXingEngine propagation — that was the source of the double/triple
        -invocation bug found in the jinye/shen stress test."""

    def receive_signal(self, resources: ResourcePool, signal: "Signal") -> None:
        """External regulatory input from ChannelGraph propagation or a
        WuXingEngine generative/control cycle, now carrying its KIND (see
        Signal). Default no-op: connectivity edges and Five Element
        relationships carry no functional effect until a component defines
        what each signal KIND means for it. Override this, not regulate(),
        and branch on signal.kind."""
        pass

    @abstractmethod
    def fail_mode(self, resources: ResourcePool) -> Optional[str]: ...


# ---------------------------------------------------------------------------
# 3. Composite — submodules share the PARENT's element allocation. This is
#    the intended behavior: Kidney's Renal/Gonadal/SkeletalMarrow submodules
#    all draw on the WATER allocation because they're one Eastern node, not
#    three independent ones.
# ---------------------------------------------------------------------------

class CompositeOrganComponent(OrganComponent):
    def __init__(self, name: str, element: Element, submodules: List[OrganComponent]):
        self.name = name
        self.element = element
        self.submodules = submodules
        for m in self.submodules:
            m.element = element  # enforce shared allocation

    def function(self, resources: ResourcePool, inputs: dict) -> dict:
        return {m.name: m.function(resources, inputs) for m in self.submodules}

    def regulate(self, resources: ResourcePool) -> None:
        for m in self.submodules:
            m.regulate(resources)

    def receive_signal(self, resources: ResourcePool, signal: "Signal") -> None:
        for m in self.submodules:
            m.receive_signal(resources, signal)

    def fail_mode(self, resources: ResourcePool) -> Optional[str]:
        modes = [m.fail_mode(resources) for m in self.submodules]
        modes = [m for m in modes if m]
        return "; ".join(modes) if modes else None


# ---------------------------------------------------------------------------
# 4. Cross-cutting regulator — Liver-Qi stagnation now checks LIVER'S OWN
#    (Wood) allocation specifically, and — if stagnant — drains every OTHER
#    organ's local qi a little. This is the same "collateral" effect the
#    old global-pool bug produced by accident, but now it's an intentional,
#    labeled mechanism (impaired systemic qi flow) instead of an artifact.
# ---------------------------------------------------------------------------

class CrossCuttingRegulator(ABC):
    name: str

    @abstractmethod
    def intercept(self, resources: ResourcePool, target: OrganComponent) -> None: ...


class LiverQiRegulator(CrossCuttingRegulator):
    name = "LiverQiFlow"
    SOURCE = Element.WOOD
    STAGNATION_THRESHOLD = 30.0
    LEAK = 0.1

    def intercept(self, resources: ResourcePool, target: OrganComponent) -> None:
        if target.element == self.SOURCE:
            return  # Liver doesn't leak onto itself
        if resources.qi_of(self.SOURCE) < self.STAGNATION_THRESHOLD:
            resources.adjust_qi(target.element, -self.LEAK)


# ---------------------------------------------------------------------------
# 5. Connectivity layer — Jing-Luo meridian network. Unchanged; it already
#    only calls regulate() on named targets, never touched the shared scalar.
# ---------------------------------------------------------------------------

@dataclass
class ChannelGraph:
    edges: List[tuple] = field(default_factory=list)

    def connect(self, source: str, target: str) -> None:
        self.edges.append((source, target))

    def propagate(self, source: str, components: Dict[str, OrganComponent],
                   resources: ResourcePool) -> None:
        for s, t in self.edges:
            if s == source and t in components:
                components[t].receive_signal(
                    resources, Signal(SignalKind.CHANNEL, source)
                )


# ---------------------------------------------------------------------------
# Wu Xing engine — generative/control cycles now MOVE qi between the two
# specific elements involved, instead of nudging one shared number that
# every organ happened to read. This is the actual fix for the
# collateral-damage bug the stress test found.
# ---------------------------------------------------------------------------

class WuXingEngine:
    def __init__(self, components: Dict[Element, OrganComponent]):
        self.components = components

    def propagate_generative(self, resources: ResourcePool, source: Element,
                              strength: float = 1.0) -> None:
        target = GENERATIVE_CYCLE[source]
        transfer = min(strength, resources.qi_of(source))
        resources.adjust_qi(source, -transfer)
        resources.adjust_qi(target, transfer)
        self.components[target].receive_signal(
            resources, Signal(SignalKind.GENERATIVE, source.value, strength)
        )

    def propagate_control(self, resources: ResourcePool, source: Element,
                           strength: float = 1.0) -> None:
        target = CONTROL_CYCLE[source]
        transfer = min(strength, resources.qi_of(target))
        resources.adjust_qi(target, -transfer)
        resources.adjust_qi(source, transfer * 0.5)  # partial return, not pure theft
        self.components[target].receive_signal(
            resources, Signal(SignalKind.CONTROL, source.value, strength)
        )


# ===========================================================================
# Reference implementations
# ===========================================================================

class Heart(OrganComponent):
    name = "Heart"
    element = Element.FIRE

    def function(self, resources, inputs):
        return {"pressure": inputs.get("venous_return", 1.0) * 1.0}

    def regulate(self, resources):
        resources.adjust(shen=0.5)

    def receive_signal(self, resources, signal):
        # Heart houses Shen. Nourished by Wood (Sheng) -> houses more shen;
        # cooled/restrained by Water (Ke: "Water controls Fire") -> shen settles.
        if signal.kind is SignalKind.GENERATIVE:
            resources.adjust(shen=+0.4 * signal.strength)
        elif signal.kind is SignalKind.CONTROL:
            resources.adjust(shen=-0.4 * signal.strength)

    def fail_mode(self, resources):
        return "Heart Blood deficiency" if resources.blood < 20 else None


class Lung(OrganComponent):
    name = "Lung"
    element = Element.METAL

    def function(self, resources, inputs):
        return {"gas_exchange": inputs.get("air_intake", 1.0)}

    def regulate(self, resources):
        resources.adjust_qi(self.element, 0.5)

    def receive_signal(self, resources, signal):
        # Lung disperses fluids (Jinye). Nourished by Earth (Sheng) -> better
        # dispersal; restrained by Fire (Ke: "Fire melts Metal") -> impaired.
        if signal.kind is SignalKind.GENERATIVE:
            resources.adjust(jinye=+0.3 * signal.strength)
        elif signal.kind is SignalKind.CONTROL:
            resources.adjust(jinye=-0.3 * signal.strength)

    def fail_mode(self, resources):
        return "Lung Qi deficiency" if resources.qi_of(self.element) < 20 else None


class Liver(OrganComponent):
    name = "Liver"
    element = Element.WOOD

    def function(self, resources, inputs):
        return {"blood_storage": resources.blood}

    def regulate(self, resources):
        pass

    def receive_signal(self, resources, signal):
        # Liver stores Blood + governs free flow of Qi. Nourished by Water
        # (Sheng) -> stores more blood; restrained by Metal (Ke: "Metal chops
        # Wood") -> constrained flow, releases stored blood.
        if signal.kind is SignalKind.GENERATIVE:
            resources.contribute_blood(self.name, +0.3 * signal.strength)
        elif signal.kind is SignalKind.CONTROL:
            resources.contribute_blood(self.name, -0.3 * signal.strength)

    def fail_mode(self, resources):
        return None


class RenalModule(OrganComponent):
    name = "Renal"
    element = Element.WATER
    def function(self, resources, inputs): return {"filtration": 1.0}
    def regulate(self, resources): resources.adjust(jinye=0.3)
    def receive_signal(self, resources, signal):
        # Kidney governs fluids (Jinye). Nourished by Metal (Sheng); restrained
        # by Earth (Ke: "Earth dams Water") -> fluid impairment.
        if signal.kind is SignalKind.GENERATIVE:
            resources.adjust(jinye=+0.3 * signal.strength)
        elif signal.kind is SignalKind.CONTROL:
            resources.adjust(jinye=-0.3 * signal.strength)
    def fail_mode(self, resources): return "CKD" if resources.jinye < 15 else None

class GonadalModule(OrganComponent):
    name = "Gonadal"
    element = Element.WATER
    def function(self, resources, inputs): return {"reproductive_capacity": 1.0}
    def regulate(self, resources): pass
    def fail_mode(self, resources): return None

class SkeletalMarrowModule(OrganComponent):
    name = "SkeletalMarrow"
    element = Element.WATER
    def function(self, resources, inputs): return {"hematopoiesis": 1.0}
    def regulate(self, resources): resources.contribute_blood(self.name, 0.2)
    def receive_signal(self, resources, signal):
        # Marrow makes blood. Nourished by Metal (Sheng) -> more; restrained by
        # Earth (Ke) -> stalled marrow contribution (visible via attribution).
        if signal.kind is SignalKind.GENERATIVE:
            resources.contribute_blood(self.name, +0.2 * signal.strength)
        elif signal.kind is SignalKind.CONTROL:
            resources.contribute_blood(self.name, -0.2 * signal.strength)
    def fail_mode(self, resources):
        contrib = resources.blood_contributions.get(self.name)
        if contrib is not None and contrib <= 0.0:
            return "Kidney Jing deficiency (marrow blood contribution stalled)"
        return None

Kidney = CompositeOrganComponent(
    name="Kidney", element=Element.WATER,
    submodules=[RenalModule(), GonadalModule(), SkeletalMarrowModule()],
)


class SpleenTransportModule(OrganComponent):
    name = "SpleenTransport"
    element = Element.EARTH
    def function(self, resources, inputs): return {"nutrient_extraction": 1.0}
    def regulate(self, resources):
        resources.adjust_qi(self.element, 0.3)
        resources.contribute_blood(self.name, 0.2)  # overlaps Kidney's blood claim, intentional — now attributed
    def receive_signal(self, resources, signal):
        # Spleen transports nutrients + makes blood. Nourished by Fire (Sheng).
        # Restrained by Wood (Ke: "Wood overacts on Earth") -> digestive/
        # hematopoietic impairment. THIS is the mechanism the general stress
        # test probes (Liver Qi stagnation -> Wood controls Earth -> Spleen
        # dysfunction); until v1.2 receive_signal was a no-op, so that scenario
        # had no code behind it.
        if signal.kind is SignalKind.GENERATIVE:
            resources.contribute_blood(self.name, +0.2 * signal.strength)
        elif signal.kind is SignalKind.CONTROL:
            resources.contribute_blood(self.name, -0.3 * signal.strength)
    def fail_mode(self, resources): return None

class SpleenHemostasisModule(OrganComponent):
    name = "SpleenHemostasis"
    element = Element.EARTH
    def function(self, resources, inputs): return {"blood_containment": 1.0}
    def regulate(self, resources): pass
    def fail_mode(self, resources): return None

Spleen = CompositeOrganComponent(
    name="Spleen", element=Element.EARTH,
    submodules=[SpleenTransportModule(), SpleenHemostasisModule()],
)


# ===========================================================================
# Demo wiring
# ===========================================================================

if __name__ == "__main__":
    resources = ResourcePool()
    heart, lung, liver = Heart(), Lung(), Liver()

    components = {
        Element.FIRE: heart,
        Element.METAL: lung,
        Element.WOOD: liver,
        Element.WATER: Kidney,
        Element.EARTH: Spleen,
    }

    graph = ChannelGraph()
    graph.connect("Heart", "Kidney")
    graph.connect("Lung", "Spleen")

    liver_qi = LiverQiRegulator()
    engine = WuXingEngine(components)

    for comp in components.values():
        comp.regulate(resources)
        liver_qi.intercept(resources, comp)

    engine.propagate_generative(resources, Element.WOOD)
    graph.propagate("Heart", {c.name: c for c in components.values()}, resources)

    print("Per-element qi:", {e.name: round(v, 1) for e, v in resources.qi_by_element.items()})
    print("blood/jinye/shen:", resources.blood, resources.jinye, resources.shen)
