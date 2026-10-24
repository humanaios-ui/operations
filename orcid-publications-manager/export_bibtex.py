import orcid_works as ow
from utils.orcid_client import OrcidClient
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from rich.console import Console
import config
from pathlib import Path

console = Console()

def work_to_bibtex_entry(work, group_dois=()):
    """Convert ORCID work detail to a BibTeX entry (null-safe).

    `group_dois` are the self DOIs of the work's whole ORCID group, used when
    the chosen representation carries none of its own.
    """
    entry = {}

    entry["title"] = ow.dig(work, "title", "title", "value") or "Untitled"
    entry["ID"] = f"orcid_{work.get('put-code', 'unknown')}"
    entry["ENTRYTYPE"] = ow.bibtex_type(work.get("type"))

    authors = ow.contributor_names(work)
    if authors:
        entry["author"] = " and ".join(authors)

    year = ow.dig(work, "publication-date", "year", "value")
    if year:
        entry["year"] = str(year)

    # ORCID v3 keys are external-id-type / external-id-value; only the
    # work's own ("self") DOI belongs in its citation.
    dois = ow.self_dois(work.get("external-ids")) or list(group_dois)
    if dois:
        entry["doi"] = dois[0]

    journal = ow.dig(work, "journal-title", "value")
    if journal:
        entry["journal"] = journal

    return entry


def main():
    client = OrcidClient()
    console.print("[bold green]Exporting works to BibTeX...[/bold green]")
    
    works_summary = client.get_works_summary()
    groups = works_summary.get("group", [])
    
    db = BibDatabase()
    db.entries = []
    
    for group in groups:
        # One entry per ORCID group: its preferred representation.
        summaries = [s for s in (ow.dig(group, "work-summary") or []) if isinstance(s, dict)]
        if not summaries:
            continue
        summary = ow.preferred(summaries)
        try:
            # Get full details for better BibTeX
            full_work = client.get_work_details(summary["put-code"])
            bib_entry = work_to_bibtex_entry(full_work, ow.group_self_dois(group))
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