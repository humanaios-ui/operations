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
    resources = ResourcePool()
    for _ in range(5):
        for component in _fresh_components().values():
            component.regulate(resources)

    assert 0.0 <= resources.shen <= 100.0
    assert 0.0 <= resources.jinye <= 100.0
    assert 0.0 <= resources.blood <= 100.0
    for element in Element:
        assert 0.0 <= resources.qi_of(element) <= 100.0


def test_S2_signal_semantics() -> None:
    resources_generative = ResourcePool()
    resources_control = ResourcePool()
    heart = Heart()

    # Canonical B1 uses small nudges (±0.4·strength) clamped to [0,100]; start from
    # a depleted baseline so directional movement is observable (a full pool clamps).
    resources_generative.shen = 50.0
    resources_control.shen = 50.0

    heart.receive_signal(resources_generative, Signal(SignalKind.GENERATIVE, "Wood", 2.0))
    heart.receive_signal(resources_control, Signal(SignalKind.CONTROL, "Water", 2.0))

    assert resources_generative.shen > 50.0
    assert resources_control.shen < 50.0


def test_S3_distributed_resilience() -> None:
    resources_peripheral = ResourcePool()
    resources_peripheral.jinye = 0.0
    resources_coordinator = ResourcePool()
    resources_coordinator.shen = 0.0

    coherence_peripheral = WuShen.assemble(resources_peripheral)["coherence"]
    coherence_coordinator = WuShen.assemble(resources_coordinator)["coherence"]

    assert coherence_peripheral > 0.0
    assert coherence_coordinator < coherence_peripheral


def test_S4_resource_clamp_invariants() -> None:
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
    resources = ResourcePool()
    lung = Lung()
    resources.jinye = 50.0  # depleted baseline: canonical nudges are small + clamped
    before = resources.jinye
    lung.receive_signal(resources, Signal(SignalKind.GENERATIVE, "Earth", 1.5))
    after_generative = resources.jinye
    lung.receive_signal(resources, Signal(SignalKind.CONTROL, "Fire", 1.5))
    after_control = resources.jinye

    assert after_generative > before
    assert after_control < after_generative


def test_S6_composite_signal_fanout() -> None:
    resources = ResourcePool()
    spleen = _fresh_spleen()
    spleen.receive_signal(resources, Signal(SignalKind.CONTROL, Element.WOOD.value, 1.0))
    assert "SpleenTransport" in resources.blood_contributions


def test_S7_sanjiao_threshold_edges() -> None:
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


def test_S9_no_regulate_on_channel_propagation() -> None:
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
        assert calls["kidney_regulate"] == 0
    finally:
        kidney.regulate = original_regulate


def test_S10_blood_attribution_dropout_detection() -> None:
    resources = ResourcePool()
    kidney = _fresh_kidney()

    marrow = [module for module in kidney.submodules if module.name == "SkeletalMarrow"][0]
    marrow.regulate(resources)
    assert resources.blood_contributions.get("SkeletalMarrow") is not None

    marrow.receive_signal(resources, Signal(SignalKind.CONTROL, Element.EARTH.value, 20.0))
    assert marrow.fail_mode(resources) is not None
