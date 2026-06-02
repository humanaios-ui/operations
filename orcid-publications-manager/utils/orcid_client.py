import requests
import json
from pathlib import Path
import config

class OrcidClient:
    def __init__(self, orcid_id=config.ORCID_ID):
        self.orcid_id = orcid_id
        self.base_url = f"https://pub.orcid.org/v3.0/{orcid_id}"
        self.headers = {
            "Accept": "application/json"
        }

    def get_record_summary(self):
        """Get summary of the entire ORCID record"""
        response = requests.get(f"{self.base_url}/record.json", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_works_summary(self):
        """Get summary list of all works (publications)"""
        response = requests.get(f"{self.base_url}/works.json", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_work_details(self, put_code):
        """Get full details of a single work by put-code"""
        response = requests.get(f"{self.base_url}/work/{put_code}", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def save_raw_data(self, data, filename="raw_works.json"):
        """Save raw JSON for inspection"""
        Path(config.DATA_DIR).mkdir(exist_ok=True)
        with open(Path(config.DATA_DIR) / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)