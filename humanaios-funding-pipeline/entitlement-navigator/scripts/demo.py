from pprint import pprint

from entitlement.catalog import load_catalog
from entitlement.engine import evaluate_profile

profile = {
    "tribal_citizen": True,
    "tribe": "Cherokee Nation",
    "outside_cn_reservation": True,
    "business_owner": True,
    "business_indian_ownership_percent": 100,
    "business_active_control": True,
    "business_seeks_capital": True,
    "dawes_ancestor_known": True,
    "deceased_ancestor_possible_trust_assets": True,
}

pprint(evaluate_profile(profile, load_catalog()))
