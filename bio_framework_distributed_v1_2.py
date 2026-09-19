from __future__ import annotations

from bio_framework_core_v1_2 import ResourcePool


class WuShen:
    @staticmethod
    def assemble(resources: ResourcePool) -> dict:
        base = (0.65 * resources.shen) + (0.35 * resources.jinye)
        coordinator_penalty = 0.0
        if resources.shen <= 5.0:
            coordinator_penalty = 15.0
        coherence = max(0.0, min(100.0, base - coordinator_penalty))
        return {"coherence": coherence}


class SanJiao:
    THRESHOLD = 25.0

    @staticmethod
    def fluid_passage(resources: ResourcePool) -> dict:
        status = "flowing" if resources.jinye >= SanJiao.THRESHOLD else "stagnant"
        return {"status": status, "jinye": resources.jinye}

    @staticmethod
    def fail_mode(resources: ResourcePool):
        if resources.jinye < SanJiao.THRESHOLD:
            return {
                "component": "SanJiao",
                "reason": "fluid_stagnation",
                "jinye": resources.jinye,
            }
        return None
