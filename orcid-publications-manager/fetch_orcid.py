import datetime
import json

from rich.console import Console

import config
import orcid_works as ow
from utils.orcid_client import OrcidClient

console = Console()


def main():
    client = OrcidClient()

    console.print(f"[bold green]Fetching ORCID data for {config.ORCID_ID}...[/bold green]")

    # Summary
    summary = client.get_record_summary()
    name = ow.dig(summary, "person", "name", "credit-name", "value") or "N/A"
    console.print(f"[cyan]Name:[/cyan] {name}")

    # Works: one record per ORCID group, so a work with several
    # representations (e.g. added by two sources) is listed once.
    raw = client.get_works_raw()
    works_summary = json.loads(raw)
    fetched_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = ow.normalize_works(works_summary, config.ORCID_ID, fetched_at, raw)

    console.print(f"[cyan]Total works found:[/cyan] {len(records)}")

    client.save_raw_data(works_summary, "raw_works.json")

    simple_list = [{"title": r["title"], "type": r["work_type"], "year": (r["date"] or "")[:4] or None,
                    "doi": r["doi"], "put-codes": r["orcid_put_codes"]} for r in records]
    client.save_raw_data(simple_list, "works_simple.json")

    console.print("[bold green]✓ Data successfully fetched and saved to /data/ folder[/bold green]")


if __name__ == "__main__":
    main()
