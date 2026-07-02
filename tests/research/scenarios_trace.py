"""
Traced liver-stagnation scenario — rewritten against CANONICAL bio_framework v1.2.

Canonical semantics (vs the earlier fork this replaces):
  - LiverQiRegulator.intercept(resources, target) is a *void qi-leak middleware*:
    when Wood qi falls below STAGNATION_THRESHOLD (30.0), each non-Wood organ leaks
    LEAK qi off its own element. It does NOT return a transformed Signal. This IS the
    liver-stagnation signature — collateral leak across organs — so the trace applies
    it per-organ and records the leak deltas directly.
  - ChannelGraph.propagate(source, components, resources) takes no signal (it emits
    CHANNEL signals internally).
  - The control/generative switch keys off the regulator's own STAGNATION_THRESHOLD,
    so the trace's cycle decision matches the framework's definition of stagnation.
"""

from __future__ import annotations

from typing import Dict

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


def _effect(delta: Dict[str, float]) -> float:
    """Observed magnitude of a step — sum of absolute resource/qi deltas."""
    return sum(abs(v) for v in delta.values())


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
    threshold = regulator.STAGNATION_THRESHOLD  # canonical stagnation definition (30.0)

    graph = ChannelGraph()
    graph.connect("Heart", "Kidney")
    graph.connect("Lung", "Spleen")
    by_name = {component.name: component for component in components.values()}

    first_failures: Dict[str, int] = {}

    def _record(tick, name, action, before, after, *, signal=None, metadata=None):
        tracer.record(
            TraceEvent(
                tick=tick,
                component=name,
                action=action,
                before=before,
                after=after,
                delta=diff(before, after),
                signal=signal,
                metadata=metadata,
            )
        )

    for tick in range(ticks):
        # 1) External Wood stressor — drives the Liver toward stagnation.
        before = snapshot(resources)
        resources.adjust_qi(Element.WOOD, -stressor)
        after = snapshot(resources)
        _record(
            tick, "external", "wood_stress", before, after,
            signal={"source": "external_wood_stress", "strength": stressor},
        )

        # 2) Each organ regulates (self-repair); capture fail modes.
        for component in components.values():
            before = snapshot(resources)
            component.regulate(resources)
            after = snapshot(resources)
            failure = component.fail_mode(resources)
            _record(
                tick, component.name, "regulate", before, after,
                metadata={"failure": failure} if failure else None,
            )
            if failure and component.name not in first_failures:
                first_failures[component.name] = tick

        wood_qi = resources.qi_of(Element.WOOD)
        stagnant = wood_qi < threshold

        # 3) Liver-Qi interception middleware — the collateral leak. When Wood is
        #    stagnant, each non-Wood organ bleeds LEAK qi off its own element.
        #    intercept() self-skips the Wood organ (target.element == SOURCE).
        for component in components.values():
            before = snapshot(resources)
            regulator.intercept(resources, component)
            after = snapshot(resources)
            leak = _effect(diff(before, after))
            _record(
                tick, component.name, "liver_qi_intercept", before, after,
                signal={"source": "LiverQiFlow", "strength": leak},
                metadata={"stagnant": stagnant, "wood_qi": wood_qi},
            )

        # 4) Wu Xing cycle decision, keyed off the same stagnation threshold:
        #    stagnant -> CONTROL (Wood restrained), else GENERATIVE (Wood nourishes Fire).
        strength = 2.0
        before = snapshot(resources)
        if stagnant:
            action = "control"
            engine.propagate_control(resources, Element.WOOD, strength)
        else:
            action = "generative"
            engine.propagate_generative(resources, Element.WOOD, strength)
        after = snapshot(resources)
        _record(
            tick, "WuXing", f"wuxing_{action}", before, after,
            signal={"source": f"wuxing_{action}", "strength": strength},
            metadata={"stagnant": stagnant, "wood_qi": wood_qi},
        )

        # 5) Meridian propagation from Heart and Lung (canonical 3-arg propagate,
        #    which emits CHANNEL signals internally). Record observed effect per source.
        for src in ("Heart", "Lung"):
            before = snapshot(resources)
            graph.propagate(src, by_name, resources)
            after = snapshot(resources)
            delta = diff(before, after)
            _record(
                tick, src, "channel_propagate", before, after,
                signal={"source": src, "kind": "channel", "strength": _effect(delta)},
                metadata={"wuxing_action": action, "wood_qi": wood_qi},
            )

    path = tracer.write_jsonl(out_path)
    return {
        "trace_path": str(path),
        "first_failures": first_failures,
        "ticks": ticks,
    }
