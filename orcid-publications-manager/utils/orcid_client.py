import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

class OrcidClient:
    def __init__(self, orcid_id="0009-0003-7540-4245"):
        self.orcid_id = orcid_id
        self.base_url = f"https://pub.orcid.org/v3.0/{orcid_id}"
        self.headers = {
            'Accept': 'application/json'
        }
    
    def get_record_summary(self):
        response = requests.get(self.base_url + "/record.json", headers=self.headers)
        return response.json() if response.ok else None
    
    def get_works(self):
        """Fetch all works/publications"""
        response = requests.get(self.base_url + "/works.json", headers=self.headers)
        return response.json() if response.ok else None