import datetime
import email.utils
import json
import time
from pathlib import Path

import requests

import config

RETRY_STATUS = {429, 500, 502, 503, 504}


def retry_after_seconds(value, now=None):
    """Retry-After as seconds: delta-seconds or an HTTP-date. None if absent/invalid."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return max(0.0, (when - now).total_seconds())


class OrcidClient:
    """Read-only client for the ORCID public API (pub.orcid.org).

    Every request has a timeout. 429 and 5xx responses, timeouts and
    connection errors are retried a bounded number of times with
    exponential backoff; anything else raises. A Retry-After (seconds or
    HTTP-date) is honoured in full. If it asks for longer than `max_wait`,
    the error is raised instead of retrying before the server is ready.
    """

    def __init__(self, orcid_id=config.ORCID_ID, timeout=20, max_attempts=4,
                 backoff=2.0, max_wait=60.0, session=None, sleep=time.sleep):
        self.orcid_id = orcid_id
        self.base_url = f"https://pub.orcid.org/v3.0/{orcid_id}"
        self.headers = {"Accept": "application/json"}
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff = backoff
        self.max_wait = max_wait
        self.session = session or requests.Session()
        self.sleep = sleep

    def _get(self, path):
        url = f"{self.base_url}/{path}"
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError):
                if attempt == self.max_attempts:
                    raise
                self.sleep(self.backoff ** attempt)
                continue
            if response.status_code in RETRY_STATUS and attempt < self.max_attempts:
                asked = retry_after_seconds(response.headers.get("Retry-After"))
                if asked is not None and asked > self.max_wait:
                    response.raise_for_status()  # server wants longer than we wait
                self.sleep(asked if asked is not None else self.backoff ** attempt)
                continue
            response.raise_for_status()
            return response
        raise RuntimeError(f"unreachable: {url}")

    def get_record_summary(self):
        """Get summary of the entire ORCID record"""
        return self._get("record").json()

    def get_works_raw(self):
        """Raw /works response body, so callers can hash exactly what ORCID sent."""
        return self._get("works").content

    def get_works_summary(self):
        """Get summary list of all works (publications)"""
        return json.loads(self.get_works_raw())

    def get_work_details(self, put_code):
        """Get full details of a single work by put-code"""
        return self._get(f"work/{put_code}").json()

    def save_raw_data(self, data, filename="raw_works.json"):
        """Save raw JSON for inspection (local data/ only; never commit it)"""
        Path(config.DATA_DIR).mkdir(exist_ok=True)
        with open(Path(config.DATA_DIR) / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
