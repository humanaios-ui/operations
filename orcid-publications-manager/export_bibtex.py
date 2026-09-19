from utils.orcid_client import OrcidClient
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from rich.console import Console
import config
from pathlib import Path

console = Console()

def work_to_bibtex_entry(work):
    """Convert ORCID work to BibTeX entry"""
    entry = {}
    
    title = work.get("title", {}).get("title", {}).get("value", "Untitled")
    entry["title"] = title
    entry["ID"] = f"orcid_{work.get('put-code', 'unknown')}"
    entry["ENTRYTYPE"] = work.get("type", "article").lower().replace("-", "")
    
    # Authors
    contributors = work.get("contributors", {}).get("contributor", [])
    if contributors:
        authors = []
        for c in contributors:
            name = c.get("credit-name", {}).get("value")
            if name:
                authors.append(name)
        entry["author"] = " and ".join(authors)
    
    # Year, DOI, etc.
    pub_date = work.get("publication-date", {})
    if pub_date.get("year", {}).get("value"):
        entry["year"] = pub_date["year"]["value"]
    
    if work.get("external-ids", {}).get("external-id"):
        for ext in work["external-ids"]["external-id"]:
            if ext.get("type") == "doi":
                entry["doi"] = ext.get("value")
    
    if work.get("journal-title", {}).get("value"):
        entry["journal"] = work["journal-title"]["value"]
    
    return entry

def main():
    client = OrcidClient()
    console.print("[bold green]Exporting works to BibTeX...[/bold green]")
    
    works_summary = client.get_works_summary()
    groups = works_summary.get("group", [])
    
    db = BibDatabase()
    db.entries = []
    
    for group in groups:
        for summary in group.get("work-summary", []):
            try:
                # Get full details for better BibTeX
                full_work = client.get_work_details(summary["put-code"])
                bib_entry = work_to_bibtex_entry(full_work)
                if bib_entry:
                    db.entries.append(bib_entry)
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not process work {summary.get('put-code')}: {e}")
    
    # Write BibTeX file
    Path(config.DATA_DIR).mkdir(exist_ok=True)
    bib_path = Path(config.DATA_DIR) / "publications.bib"
    
    writer = BibTexWriter()
    writer.order_entries_by = ("year", "author")
    
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(writer.write(db))
    
    console.print(f"[bold green]✓ Exported {len(db.entries)} publications to {bib_path}[/bold green]")
    console.print("You can now use this .bib file in LaTeX, Zotero, or import back to ORCID.")

if __name__ == "__main__":
    main()