# CICD Data Summit 2026 — Reading Summary, Pre-Event Notes & Contacts

**Event:** Sovereignty in Numbers: The 2026 Center for Indian Country Development Data Summit
**Date:** June 25, 2026 · 10:00 a.m.–3:00 p.m. CT · virtual
**Host:** Center for Indian Country Development (CICD), Federal Reserve Bank of Minneapolis
**Prepared:** 2026-06-05 · for Night (Zone 2)
**Status:** Internal pre-event brief. Attendance is virtual/observational. No outreach actions taken — all contact items below are Z2/Z3 decisions.

-----

## Part 1 — Reading Summary (the three linked articles)

### Article A — “Tribes innovate economic data practices based on tribal values” (June 2025, Caryn Mohr)

Part of CICD’s tenth-anniversary series. Profiles four tribes turning existing data into service decisions, with a consistent throughline: data practice rooted in tribal values, with confidentiality handled at the community level.

- **Cheyenne and Arapaho Tribes (OK)** repurposed vehicle-registration data to drive transit and food-distribution decisions. Governor Reggie Wassana stressed confidentiality: registration data stay inside the collecting office, and other departments receive only de-identified aggregate counts. The privacy architecture is a design choice, not an afterthought.
- **Navajo Nation** ran a 5,000+ response Hardship Consumer Impact Survey during COVID, learning ~60% of relief funds were spent off-nation. Economist Alisha Murphy’s lesson: “When you want quality data, it’s not going to be fast, and it’s not going to be cheap. We need to take the time to build relationships and collaboration.”
- **Red Cliff Band of Lake Superior Chippewa (WI)** runs a five-year tribal census (90% response rate in 2023) using a four-digit per-household code that tracks completion without collecting names or addresses — privacy-preserving identifier design. Census feeds directly into housing decisions.
- **Chickasaw Nation (OK)** is mapping its internal data ecosystem under inaugural data-stewardship director Mari Hulbutta — identifying data domains and custodians, moving “from program-centric data to citizen-centric data.”

**Why it matters for us:** Every example pairs data utility with a deliberate privacy/identifier architecture. This is structurally the same discipline as ACAT’s submission-purity, anonymous-token raters, and two-corpus separation — utility without exposure. The vocabulary the room uses is “data on our own terms,” “citizen-centric,” “data custodians.”

### Article B — “A new era for Indigenous data sovereignty” (Dec 2024, Caryn Mohr)

Recap of the 2024 CICD summit; the conceptual anchor for the whole series. Built around a fireside chat with **Stephanie Russo Carroll** (Collaboratory for Indigenous Data Governance).

- Carroll’s definition: Indigenous data sovereignty is “the right to govern the collection, application, storage, and use of data about us as individuals and collectives… Fundamentally, it’s about the inherent sovereignty that Indigenous peoples have.”
- Key frameworks named: the **CARE Principles** (Collective Benefit, Authority to Control, Responsibility, Ethics) from the Global Indigenous Data Alliance; the **CARE Data Maturity Model**; the **U.S. Indigenous Data Sovereignty Network**; the **Center for Tribal Digital Sovereignty** (AIPI / NCAI, 2024); and **CICD’s own Principles for Research and Data Use** (2022).
- A historical warning from Chrystel Cornelius (Oweesta): an 1800s census undercounted the Turtle Mountain Band, shrinking their land base. “Data haven’t always been our friend.” Non-Native researchers carry an obligation to understand how data has been used against tribal sovereignty.
- Carroll’s framing of the movement as inclusive rather than gatekeeping: “There’s a role for everybody — for elders, for youth, for scholars. It’s not a competitive space… It’s a synergistic space in which to be a good relative.”

**Why it matters for us:** This is the article to internalize most. CARE is the live governance vocabulary. The “good relative” framing and the historical-harm context define the posture any external party should hold: arrive as a learner and a good relative, not a vendor. The Cornelius example is the cautionary tale against extractive data practice — directly relevant to how ACAT must position if it ever touches community data.

### Article C — “Three ways economic data will strengthen Indian Country over the next decade” (Feb 2026, Casey Lozar)

Forward-looking essay by the CICD director (the summit’s opening voice). Three predicted advances:

1. **Tribal and intertribal data** — more tribes running their own censuses; growth of intertribal datasets (e.g., the Survey of Native Nations) built on trust and data-sharing among tribes.
1. **Data lakes accessible across tribal government** — harmonized repositories that let administrators across functions make evidence-based decisions; tribes investing in research staff and data departments as core government functions.
1. **Shaping AI around data sovereignty** — Lozar’s most directly relevant section: tribes will use AI to analyze data and deploy insights, but “given Indian Country’s historical experiences with our data being used in ways that harmed our communities, it will be vital for tribes to lead the way in shaping AI applications in alignment with data-sovereignty principles.” He points to the OU Native Nations Center’s work on tribal AI governance.

**Why it matters for us:** Section 3 is the exact thesis-space the “AI on Indigenous Terms” panel will occupy. Lozar frames AI adoption as something tribes lead and shape on sovereignty terms — not something done to them. ACAT’s posture (measuring whether AI systems behave as they claim; detection over compliance) is conceptually adjacent: both are about holding AI accountable to a community’s terms rather than a vendor’s claims. That adjacency is the honest bridge — and it must stay framed as adjacency, not as a solution offered.

-----

## Part 2 — Pre-Event Notes: ACAT Data-Sovereignty Posture vs. “AI on Indigenous Terms”

**Panel:** AI on Indigenous Terms: Considerations for Indian Country · 11:00 a.m.–12:00 p.m. CT
**Moderator:** Vanessa Palmer (CICD Division Data Director) · **Panelist:** Michael Running Wolf (First Languages AI Reality) · additional speakers TBA

### The framing the panel will use

Based on Article C and Running Wolf’s profile, the panel’s frame is: *AI is arriving in Indian Country; tribes intend to engage it on their own sovereignty terms; the open question is how to do so without repeating historical data harms.* CARE principles and “data on our own terms” are the governing vocabulary.

### Where ACAT genuinely aligns (defensible)

1. **Detection over compliance (P19) ≈ “lead the way in shaping AI applications.”** Both reject the posture of trusting a vendor’s claims about an AI system. ACAT measures the gap between what an AI says about itself and what it demonstrates. Tribal data sovereignty asks who controls and verifies the terms of AI use. The shared root: accountability sits with the party affected, not the party deploying.
1. **Behavioral observability ≈ “shaping AI on our own terms.”** A community cannot govern an AI system it cannot observe. ACAT is being developed as a behavioral telemetry layer — a way to see how a system actually behaves across dimensions like truthfulness, humility, and harm-awareness. That observability is a precondition for any community setting terms on AI it deploys.
1. **Open, auditable methodology ≈ CARE “Authority to Control” + “Responsibility.”** ACAT’s instrument, dataset, and corrections ledger are public and Apache-2.0. The methodological transparency means a tribe (or any party) could inspect and adapt the instrument rather than trust a black box — consistent with the CARE emphasis on authority and accountability.
1. **Anonymity and privacy architecture ≈ the confidentiality designs in Article A.** ACAT’s anonymous-token raters, submission-purity constraints, and two-corpus separation mirror the de-identified-aggregate and per-household-code patterns the tribes described. Same discipline: utility without exposure.

### Where the alignment must NOT be overstated (the honest limits)

- **ACAT does not address data sovereignty as the movement defines it.** Indigenous data sovereignty is about governance of data *about Indigenous people and collectives*. ACAT measures the behavior of *AI systems*. These are adjacent concerns, not the same concern. Conflating them would be a category error and would read as appropriation of the sovereignty frame for a product.
- **ACAT is TRL 2–3.** It is being developed as infrastructure; it is not a deployed, validated governance tool. Any framing must say “being developed as,” not “is.”
- **No community data is involved, and none should be implied.** ACAT’s corpus is AI self-assessments, not data about any community. There is no existing tribal-data application to claim.
- **The CARE “Collective Benefit” test is unmet by default.** ACAT was not built with or for any tribal community. Claiming benefit to Indian Country without a relationship and invitation would violate the exact “good relative” principle Carroll names.

### Posture for attending (the “good relative” stance)

- Attend as a **learner**, not a vendor. The room’s explicit norm (Carroll) is synergistic, not competitive — but that welcome is for people who arrive to contribute and listen, not to pitch.
- The honest one-line framing, if ever asked: *“I run an open-source project measuring whether AI systems behave the way they claim to — which feels adjacent to the sovereignty question of governing AI on a community’s own terms, and I came to learn how that work is being thought about here.”*
- **No outreach during or immediately after the event.** Per Tradition 11 (attraction not promotion) and P-ANON, any contact is a deliberate, later Z2 decision — not a reaction to the panel.
- Note the founder’s Cherokee Nation citizenship is real context, but it does not by itself create standing to claim alignment between ACAT and tribal data sovereignty. Relationship and invitation do.

### Listening targets during the panel (what to capture)

- How Running Wolf frames “ethical application of AI in respect of Indigenous data sovereignty” — his FLAIR language-reclamation work is the concrete case study.
- Whether anyone names a verification or accountability gap in AI tools tribes are adopting — that is the one place ACAT’s actual function is genuinely responsive.
- Which governance frameworks get cited live (CARE, OU Native Nations Center tribal AI governance, AIPI Center for Tribal Digital Sovereignty) — these are the canonical references to read after, not before, forming any view.

-----

## Part 3 — Contacts (public-facing only; alignment with the human-collaboration mission)

**P-ANON / Tradition 11 note:** These are publicly listed professional affiliations from the event page and public org pages. No private contact details are recorded here. Any outreach is a Z2 decision made deliberately and later — not a same-day reaction to the summit. Inclusion here is for *alignment mapping*, not a call list.

### Most aligned with the AI × data-sovereignty intersection

- **Traci Morris** (Chickasaw Nation) — Executive Director, American Indian Policy Institute, Sandra Day O’Connor College of Law, Arizona State University. Leading scholar in tribal digital sovereignty; research on data governance and AI in Indian Country. AIPI also co-launched the Center for Tribal Digital Sovereignty. *Public channel: AIPI at ASU (aipi.asu.edu).* — The single most topically aligned person on the roster for the research/academic-host angle.
- **Michael Running Wolf** (Lakota, Cheyenne) — Co-Founder & Lead Architect, First Languages AI Reality (FLAIR). Former Amazon Alexa engineer; ethical AI + Indigenous data sovereignty. *Public channel: FLAIR organization.* — Closest to the applied-AI-ethics practitioner profile; relevant to the human-collaboration mission (language reclamation is human-in-the-loop AI work).
- **Stephanie Russo Carroll** (Ahtna–Native Village of Kluti-Kaah) — Director, Collaboratory for Indigenous Data Governance (University of Arizona); CICD Leadership Council. Architect of CARE-principles implementation work and the CARE Data Maturity Model. *Public channel: Collaboratory / indigenousdatalab.org.* — Not a summit speaker this year, but the field’s governance authority; the right source to *read*, and the standard any ACAT-adjacent claim would be measured against.

### CDFI / community-finance alignment (relevant to the Trinity / recovery-funding mission)

- **Lakota Vogel** (Cheyenne River Sioux) — Executive Director, Four Bands Community Fund; Minneapolis Fed Board of Directors. Native CDFI leadership; led a coalition to a $45M EDA award. *Public channel: Four Bands Community Fund.*
- **Ted Piccolo** (Colville) — Senior Director of Indigenous Futures, Mission Driven Finance; founding ED of the first Native CDFI in eastern Washington. *Public channel: Mission Driven Finance.*
- **Mike Lettig** (Navajo descent) — Group Head, Native American Financial Services, Huntington Bank. Decades of Indian Country capital work. *Public channel: Huntington Bank.*

### CICD institutional contacts (host org)

- **Casey Lozar** (Confederated Salish and Kootenai) — VP, Minneapolis Fed; Director, CICD. The summit’s lead. CICD has a public **Speakers Bureau / request-a-speaker** form and a **Contact CICD** page (minneapolisfed.org/indiancountry/contact-cicd) — the correct, public, front-door channel for any institutional contact, rather than approaching individuals directly.
- **Vanessa Palmer** — CICD Division Data Director; moderates the AI panel. Data-practice and harmonization lead.
- **H Trostle** (Cherokee Nation) — CICD Senior Policy Analyst; leads the Survey of Native Nations. Cherokee Nation connection; fiscal-data focus.

### Suggested protocol if any contact is later approved (Z2)

1. Read CARE principles and CICD’s Principles for Research and Data Use *first* — before any message.
1. Front door before individuals: the CICD Contact page / Speakers Bureau is the public, respectful channel.
1. Lead as a learner and a good relative; do not lead with ACAT as a solution.
1. Run the P-ANON check — no collaborator or community data on any public surface.
1. Keep TRL 2–3 framing in any description of ACAT.

-----

## Open items / honest gaps

- The AI panel and the land-acquisition panel both list **additional speakers TBA** — re-check the event page closer to June 25 for the full AI roster.
- I did not verify current direct contact details for any individual; only public organizational affiliations are recorded, by design.
- Whether any of these alignments should convert to outreach is entirely a Z2 decision and explicitly out of scope for this brief.

*Prepared by Unit Zero (Zone 1) for Night (Zone 2). Sources: Minneapolis Fed CICD event and article pages (fetched 2026-06-05). For placement: `operations/docs/CICD_SUMMIT_2026_BRIEF.md`*