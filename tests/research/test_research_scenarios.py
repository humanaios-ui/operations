from __future__ import annotations

from typing import Dict

from bio_framework_core_v1_2 import (
    ChannelGraph,
    CompositeOrganComponent,
    Element,
    GonadalModule,
    Heart,
    Liver,
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
from bio_framework_distributed_v1_2 import SanJiao, WuShen


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


def test_S1_baseline_homeostasis() -> None:
    """Verify homeostatic regulation maintains resource bounds over 5 ticks.
    Uses a single fresh component set to verify systemic stability."""
    resources = ResourcePool()
    components = _fresh_components()
    for _ in range(5):
        for component in components.values():
            component.regulate(resources)

    assert 0.0 <= resources.shen <= 100.0
    assert 0.0 <= resources.jinye <= 100.0
    assert 0.0 <= resources.blood <= 100.0
    for element in Element:
        assert 0.0 <= resources.qi_of(element) <= 100.0


def test_S2_signal_semantics() -> None:
    """Verify signal semantics: GENERATIVE increases shen, CONTROL decreases.
    Heart.receive_signal multiplies signal.strength by 0.4 (shen nudge).
    With transfer=2.0: 50.0 + (0.4 × 2.0) = 50.8 (observable margin)."""
    resources_generative = ResourcePool()
    resources_control = ResourcePool()
    heart = Heart()

    # Start from baseline to ensure nudges are observable (not clamped by 100.0).
    resources_generative.shen = 50.0
    resources_control.shen = 50.0

    heart.receive_signal(resources_generative, Signal(SignalKind.GENERATIVE, "Wood", 2.0))
    heart.receive_signal(resources_control, Signal(SignalKind.CONTROL, "Water", 2.0))

    assert resources_generative.shen > 50.0
    assert resources_control.shen < 50.0


def test_S3_distributed_resilience() -> None:
    """Verify distributed resilience: peripheral jinye dropout has lower impact
    than coordinator shen dropout on coherence."""
    resources_peripheral = ResourcePool()
    resources_peripheral.jinye = 0.0
    resources_coordinator = ResourcePool()
    resources_coordinator.shen = 0.0

    coherence_peripheral = WuShen.assemble(resources_peripheral)["coherence"]
    coherence_coordinator = WuShen.assemble(resources_coordinator)["coherence"]

    assert coherence_peripheral > 0.0
    assert coherence_coordinator < coherence_peripheral


def test_S4_resource_clamp_invariants() -> None:
    """Verify clamping enforces [0, 100] bounds on all resources."""
    resources = ResourcePool()
    resources.adjust(shen=9999.0, jinye=9999.0, blood=9999.0)
    for element in Element:
        resources.adjust_qi(element, 9999.0)

    assert resources.shen == 100.0
    assert resources.jinye == 100.0
    assert resources.blood == 100.0
    assert all(resources.qi_of(element) == 100.0 for element in Element)

    resources.adjust(shen=-9999.0, jinye=-9999.0, blood=-9999.0)
    for element in Element:
        resources.adjust_qi(element, -9999.0)

    assert resources.shen == 0.0
    assert resources.jinye == 0.0
    assert resources.blood == 0.0
    assert all(resources.qi_of(element) == 0.0 for element in Element)


def test_S5_control_vs_generative_opposition() -> None:
    """Verify signal opposition: GENERATIVE increases jinye, CONTROL decreases.
    Lung.receive_signal multiplies signal.strength by 0.3 (jinye nudge).
    With transfer=1.5: generative +0.45, control -0.45."""
    resources = ResourcePool()
    lung = Lung()
    resources.jinye = 50.0  # Baseline: ensure nudges are observable.
    before = resources.jinye
    lung.receive_signal(resources, Signal(SignalKind.GENERATIVE, "Earth", 1.5))
    after_generative = resources.jinye
    lung.receive_signal(resources, Signal(SignalKind.CONTROL, "Fire", 1.5))
    after_control = resources.jinye

    assert after_generative > before
    assert after_control < after_generative


def test_S6_composite_signal_fanout() -> None:
    """Verify composite receives signals to submodules (fanout).
    SpleenTransport records blood attribution on CONTROL reception."""
    resources = ResourcePool()
    spleen = _fresh_spleen()
    spleen.receive_signal(resources, Signal(SignalKind.CONTROL, Element.WOOD.value, 1.0))
    assert "SpleenTransport" in resources.blood_contributions


def test_S7_sanjiao_threshold_edges() -> None:
    """Verify SanJiao fluid passage threshold at jinye >= 25.0."""
    resources = ResourcePool()

    resources.jinye = 24.99
    below = SanJiao.fluid_passage(resources)
    assert below["status"] == "stagnant"
    assert SanJiao.fail_mode(resources) is not None

    resources.jinye = 25.0
    at = SanJiao.fluid_passage(resources)
    assert at["status"] == "flowing"
    assert SanJiao.fail_mode(resources) is None

    resources.jinye = 25.01
    above = SanJiao.fluid_passage(resources)
    assert above["status"] == "flowing"


def test_S8_wuxing_transfer_conservation_like() -> None:
    """Verify generative transfer is symmetric (conservation-like).
    Transfers qi from source to target in equal amounts."""
    resources = ResourcePool()
    resources.qi_by_element = {element: 50.0 for element in Element}
    engine = WuXingEngine(_fresh_components())

    wood_before = resources.qi_of(Element.WOOD)
    fire_before = resources.qi_of(Element.FIRE)
    engine.propagate_generative(resources, Element.WOOD, strength=3.0)
    wood_after = resources.qi_of(Element.WOOD)
    fire_after = resources.qi_of(Element.FIRE)

    assert round(wood_before - wood_after, 6) == 3.0
    assert round(fire_after - fire_before, 6) == 3.0


def test_S8_control_propagation_lossy() -> None:
    """Verify control propagation is LOSSY (not symmetric conservation).
    Target loses full transfer; source gets partial return (0.5x).
    Transfer from EARTH (target) = 3.0; WOOD (source) gains 1.5 (0.5x)."""
    resources = ResourcePool()
    resources.qi_by_element = {element: 50.0 for element in Element}
    engine = WuXingEngine(_fresh_components())

    earth_before = resources.qi_of(Element.EARTH)
    wood_before = resources.qi_of(Element.WOOD)
    engine.propagate_control(resources, Element.WOOD, strength=3.0)
    earth_after = resources.qi_of(Element.EARTH)
    wood_after = resources.qi_of(Element.WOOD)

    # EARTH (target) loses 3.0
    assert round(earth_before - earth_after, 6) == 3.0
    # WOOD (source) gains 1.5, NOT 3.0 (lossy transfer)
    assert round(wood_after - wood_before, 6) == 1.5


def test_S9_no_regulate_on_channel_propagation() -> None:
    """Verify channel propagation calls receive_signal, NOT regulate.
    Wraps kidney.regulate to detect if it's invoked by channel propagation."""
    resources = ResourcePool()
    heart = Heart()
    kidney = _fresh_kidney()

    calls = {"kidney_regulate": 0}
    original_regulate = kidney.regulate

    def wrapped_regulate(payload: ResourcePool) -> None:
        calls["kidney_regulate"] += 1
        original_regulate(payload)

    kidney.regulate = wrapped_regulate
    try:
        graph = ChannelGraph()
        graph.connect("Heart", "Kidney")
        graph.propagate("Heart", {"Heart": heart, "Kidney": kidney}, resources)
        # Verify regulate was never called during propagation
        assert calls["kidney_regulate"] == 0
    finally:
        kidney.regulate = original_regulate


def test_S10_blood_attribution_dropout_detection() -> None:
    """Verify blood attribution dropout detection on marrow stalling.
    SkeletalMarrow.regulate contributes +0.2; CONTROL signal applies -0.4
    (0.2 * 2.0). Cumulative contribution: 0.2 - 0.4 = -0.2 (stalled)."""
    resources = ResourcePool()
    kidney = _fresh_kidney()

    marrow = [module for module in kidney.submodules if module.name == "SkeletalMarrow"][0]
    marrow.regulate(resources)
    # After regulate, contribution is +0.2 (cumulative)
    assert resources.blood_contributions.get("SkeletalMarrow") is not None
    assert resources.blood_contributions.get("SkeletalMarrow") == 0.2

    marrow.receive_signal(resources, Signal(SignalKind.CONTROL, Element.EARTH.value, 2.0))
    # After CONTROL, contribution is 0.2 - 0.4 = -0.2 (cumulative)
    # Fail mode triggers: contrib <= 0.0
    assert marrow.fail_mode(resources) is not None
    assert resources.blood_contributions.get("SkeletalMarrow") == -0.2
