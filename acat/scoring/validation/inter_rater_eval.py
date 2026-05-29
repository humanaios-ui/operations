def compute_inter_rater_agreement(machine_scores: dict, human_scores: dict) -> dict:
    return {
        "metric": "cohens_kappa",
        "value": None,
        "status": "pending"
    }
