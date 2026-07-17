from utils.orcid_client import OrcidClient
from rich.console import Console
import config
from pathlib import Path

console = Console()

def main():
    client = OrcidClient()
    
    console.print(f"[bold green]Fetching ORCID data for {config.ORCID_ID}...[/bold green]")
    
    # Summary
    summary = client.get_record_summary()
    console.print(f"[cyan]Name:[/cyan] {summary.get('person', {}).get('name', {}).get('credit-name', {}).get('value', 'N/A')}")
    
    # Works
    works_summary = client.get_works_summary()
    works = works_summary.get("group", [])
    
    console.print(f"[cyan]Total works found:[/cyan] {len(works)}")
    
    client.save_raw_data(works_summary, "raw_works.json")
    
    # Save basic list
    simple_list = []
    for group in works:
        for work in group.get("work-summary", []):
            simple_list.append({
                "title": work.get("title", {}).get("title", {}).get("value"),
                "type": work.get("type"),
                "year": work.get("publication-date", {}).get("year", {}).get("value"),
                "put-code": work.get("put-code")
            })
    
    client.save_raw_data(simple_list, "works_simple.json")
    
    console.print("[bold green]✓ Data successfully fetched and saved to /data/ folder[/bold green]")

if __name__ == "__main__":
    main()