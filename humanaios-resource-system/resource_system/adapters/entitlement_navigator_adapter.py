from resource_system.adapters.resource_miner_adapter import load_handoff_module

def investigate(candidate):
    handoff = load_handoff_module('resource-miner/resource_miner/entitlement_handoff.py').build_entitlement_handoff(candidate)
    return load_handoff_module('entitlement-navigator/entitlement/resource_handoff.py').intake_resource_handoff(handoff)
