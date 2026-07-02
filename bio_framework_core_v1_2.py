from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable


class Element(Enum):
    WOOD = "Wood"
    FIRE = "Fire"
    EARTH = "Earth"
    METAL = "Metal"
    WATER = "Water"


class SignalKind(Enum):
    GENERATIVE = "generative"
    CONTROL = "control"
    CHANNEL = "channel"


@dataclass(frozen=True)
class Signal:
    kind: SignalKind
    source: str
    strength: float


class ResourcePool:
    def __init__(self) -> None:
        self.shen = 50.0
        self.jinye = 50.0
        self.blood = 50.0
        self.qi_by_element: Dict[Element, float] = {element: 50.0 for element in Element}
        self.blood_contributions: Dict[str, float] = {}

    @property
    def total_qi(self) -> float:
        return sum(self.qi_by_element.values())

    def clamp(self, value: float) -> float:
        return max(0.0, min(100.0, value))

    def qi_of(self, element: Element) -> float:
        return self.qi_by_element[element]

    def adjust_qi(self, element: Element, delta: float) -> None:
        self.qi_by_element[element] = self.clamp(self.qi_by_element[element] + delta)

    def adjust(self, *, shen: float = 0.0, jinye: float = 0.0, blood: float = 0.0) -> None:
        self.shen = self.clamp(self.shen + shen)
        self.jinye = self.clamp(self.jinye + jinye)
        self.blood = self.clamp(self.blood + blood)


class OrganComponent:
    name = "Organ"
    element = Element.EARTH

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust_qi(self.element, 0.5)

    def receive_signal(self, resources: ResourcePool, signal: Signal) -> None:
        if signal.kind is SignalKind.GENERATIVE:
            self._apply_generative(resources, signal.strength)
        elif signal.kind is SignalKind.CONTROL:
            self._apply_control(resources, signal.strength)
        elif signal.kind is SignalKind.CHANNEL:
            self._apply_channel(resources, signal.strength)

    def _apply_generative(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust_qi(self.element, strength)

    def _apply_control(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust_qi(self.element, -strength)

    def _apply_channel(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust_qi(self.element, strength * 0.5)

    def fail_mode(self, resources: ResourcePool):
        return None


class Heart(OrganComponent):
    name = "Heart"
    element = Element.FIRE

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust(shen=1.0)
        resources.adjust_qi(self.element, 0.8)

    def _apply_generative(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust(shen=0.5 * strength)

    def _apply_control(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust(shen=-0.5 * strength)


class Lung(OrganComponent):
    name = "Lung"
    element = Element.METAL

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust(jinye=0.7)
        resources.adjust_qi(self.element, 0.4)

    def _apply_generative(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust(jinye=0.8 * strength)

    def _apply_control(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust(jinye=-0.8 * strength)


class Liver(OrganComponent):
    name = "Liver"
    element = Element.WOOD

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust_qi(self.element, 1.2)


class RenalModule(OrganComponent):
    name = "Renal"
    element = Element.WATER

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust(jinye=0.8)
        resources.adjust_qi(self.element, 1.0)


class GonadalModule(OrganComponent):
    name = "Gonadal"
    element = Element.WATER

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust(shen=0.4)
        resources.adjust_qi(self.element, 0.6)


class SkeletalMarrowModule(OrganComponent):
    name = "SkeletalMarrow"
    element = Element.WATER

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust(blood=1.5)
        resources.blood_contributions[self.name] = resources.blood_contributions.get(self.name, 0.0) + 1.5

    def _apply_control(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust(blood=-2.0 * strength)

    def fail_mode(self, resources: ResourcePool):
        if resources.blood_contributions.get(self.name, 0.0) <= 0.0 or resources.blood < 20.0:
            return {"component": self.name, "reason": "blood_attribution_dropout"}
        return None


class SpleenTransportModule(OrganComponent):
    name = "SpleenTransport"
    element = Element.EARTH

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust(blood=1.0)
        resources.blood_contributions[self.name] = resources.blood_contributions.get(self.name, 0.0) + 1.0

    def _apply_control(self, resources: ResourcePool, strength: float) -> None:
        resources.adjust(blood=-0.5 * strength)
        resources.blood_contributions[self.name] = resources.blood_contributions.get(self.name, 0.0) + 0.1


class SpleenHemostasisModule(OrganComponent):
    name = "SpleenHemostasis"
    element = Element.EARTH

    def regulate(self, resources: ResourcePool) -> None:
        resources.adjust_qi(self.element, 0.5)


class CompositeOrganComponent:
    def __init__(self, name: str, submodules: Iterable[OrganComponent], element: Element) -> None:
        self.name = name
        self.submodules = list(submodules)
        self.element = element

    def regulate(self, resources: ResourcePool) -> None:
        for module in self.submodules:
            module.regulate(resources)

    def receive_signal(self, resources: ResourcePool, signal: Signal) -> None:
        for module in self.submodules:
            module.receive_signal(resources, signal)

    def fail_mode(self, resources: ResourcePool):
        for module in self.submodules:
            failure = module.fail_mode(resources)
            if failure:
                return failure
        return None


Kidney = CompositeOrganComponent(
    "Kidney",
    [RenalModule(), GonadalModule(), SkeletalMarrowModule()],
    Element.WATER,
)

Spleen = CompositeOrganComponent(
    "Spleen",
    [SpleenTransportModule(), SpleenHemostasisModule()],
    Element.EARTH,
)


class LiverQiRegulator:
    def intercept(self, resources: ResourcePool, signal: Signal) -> Signal:
        if resources.qi_of(Element.WOOD) < 40.0 and signal.kind is SignalKind.CONTROL:
            return Signal(signal.kind, signal.source, signal.strength * 0.5)
        return signal


class WuXingEngine:
    _generative_cycle = {
        Element.WOOD: Element.FIRE,
        Element.FIRE: Element.EARTH,
        Element.EARTH: Element.METAL,
        Element.METAL: Element.WATER,
        Element.WATER: Element.WOOD,
    }
    _control_cycle = {
        Element.WOOD: Element.EARTH,
        Element.EARTH: Element.WATER,
        Element.WATER: Element.FIRE,
        Element.FIRE: Element.METAL,
        Element.METAL: Element.WOOD,
    }

    def __init__(self, components: Dict[Element, object]) -> None:
        self.components = components

    def propagate_generative(self, resources: ResourcePool, source: Element, strength: float) -> None:
        target = self._generative_cycle[source]
        resources.adjust_qi(source, -strength)
        resources.adjust_qi(target, strength)
        target_component = self.components.get(target)
        if target_component:
            target_component.receive_signal(resources, Signal(SignalKind.GENERATIVE, source.value, strength))

    def propagate_control(self, resources: ResourcePool, source: Element, strength: float) -> None:
        target = self._control_cycle[source]
        resources.adjust_qi(target, -strength)
        target_component = self.components.get(target)
        if target_component:
            target_component.receive_signal(resources, Signal(SignalKind.CONTROL, source.value, strength))


class ChannelGraph:
    def __init__(self) -> None:
        self._edges: Dict[str, list[str]] = {}

    def connect(self, source: str, target: str) -> None:
        self._edges.setdefault(source, []).append(target)

    def propagate(
        self,
        source: str,
        components_by_name: Dict[str, object],
        resources: ResourcePool,
        signal: Signal | None = None,
    ) -> None:
        outgoing = self._edges.get(source, [])
        base_signal = signal or Signal(SignalKind.CHANNEL, source, 1.0)
        for target in outgoing:
            component = components_by_name.get(target)
            if component:
                component.receive_signal(resources, base_signal)
