from __future__ import annotations

from typing import Dict, List

from bio_framework_core_v1_2 import (
    ChannelGraph,
    CompositeOrganComponent,
    Element,
    GonadalModule,
    Heart,
    Liver,
    LiverQiRegulator,
    Lung,
    RenalModule,
    ResourcePool,
    Signal,
    SignalKind,
    SkeletalMarrowModule,
    SpleenHemostasisModule,
    SpleenTransportModule,
    WuXingEngine,
)
from tests.research.event_trace import EventTracer, TraceEvent, diff, snapshot


def _fresh_kidney() -> CompositeOrganComponent:
    return CompositeOrganComponent(
        "Kidney",
        Element.WATER,
        [RenalModule(), GonadalModule(), SkeletalMarrowModule()],
    )


def _fresh_spleen() -> CompositeOrganComponent:
    return CompositeOrganComponent(
        "Spleen",
        Element.EARTH,
        [SpleenTransportModule(), SpleenHemostasisModule()],
    )


def _fresh_components() -> Dict[Element, object]:
    return {
        Element.FIRE: Heart(),
        Element.METAL: Lung(),
        Element.WOOD: Liver(),
        Element.WATER: _fresh_kidney(),
        Element.EARTH: _fresh_spleen(),
    }


def run_traced_liver_stagnation(
    ticks: int = 20,
    stressor: float = 5.0,
    out_path: str = "artifacts/traces/S2_liver_stagnation_trace.jsonl",
) -> dict:
    resources = ResourcePool()
    components = _fresh_components()
    tracer = EventTracer()
    engine = WuXingEngine(components)
    regulator = LiverQiRegulator()

    graph = ChannelGraph()
    graph.connect("Heart", "Kidney")
    graph.connect("Lung", "Spleen")
    by_name = {component.name: component for component in components.values()}

    first_failures: Dict[str, int] = {}

    for tick in range(ticks):
        resources.adjust_qi(Element.WOOD, -stressor)

        for component in components.values():
            before = snapshot(resources)
            component.regulate(resources)
            after = snapshot(resources)
            failure = component.fail_mode(resources)
            tracer.record(
                TraceEvent(
                    tick=tick,
                    component=component.name,
                    action="regulate",
                    before=before,
                    after=after,
                    delta=diff(before, after),
                    metadata={"failure": failure} if failure else None,
                )
            )
            if failure and component.name not in first_failures:
                first_failures[component.name] = tick

        stagnation = resources.qi_of(Element.WOOD)
        if stagnation < 40.0:
            signal = Signal(SignalKind.CONTROL, Element.WOOD.value, 2.0)
            action = "control"
            engine.propagate_control(resources, Element.WOOD, 2.0)
        else:
            signal = Signal(SignalKind.GENERATIVE, Element.WOOD.value, 2.0)
            action = "generative"
            engine.propagate_generative(resources, Element.WOOD, 2.0)

        intercepted = regulator.intercept(resources, signal)
        for src in ("Heart", "Lung"):
            before = snapshot(resources)
            graph.propagate(src, by_name, resources, intercepted)
            after = snapshot(resources)
            tracer.record(
                TraceEvent(
                    tick=tick,
                    component=src,
                    action="channel_propagate",
                    before=before,
                    after=after,
                    delta=diff(before, after),
                    signal={
                        "source": src,
                        "kind": intercepted.kind.value,
                        "strength": intercepted.strength,
                    },
                    metadata={"wuxing_action": action, "stagnation": stagnation},
                )
            )

    path = tracer.write_jsonl(out_path)
    return {
        "trace_path": str(path),
        "first_failures": first_failures,
        "ticks": ticks,
    }
