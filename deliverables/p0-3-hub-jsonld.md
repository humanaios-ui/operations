# P0-3 · Task 3 — Hub Structured Data (JSON-LD)

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Review-ready (paste into `humanaios.ai` `<head>`)
**Target:** `https://humanaios.ai/`

**Why this matters:** structured data is the strongest single signal you can give search engines that "this Person = this ORCID = author of this paper = maintainer of this dataset." It's what turns six scattered profiles into one consolidated entity — the core fix for the "Carly Anderson" collision — and it can earn rich results (dataset cards, knowledge-panel eligibility).

---

## The block — paste into `<head>` of the homepage

Drop this `<script>` verbatim into the `<head>` of `humanaios.ai` (homepage is enough; site-wide is fine too). It's one graph tying every entity together by `@id`.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://humanaios.ai/#website",
      "url": "https://humanaios.ai/",
      "name": "HumanAIOS",
      "publisher": { "@id": "https://humanaios.ai/#org" }
    },
    {
      "@type": "Organization",
      "@id": "https://humanaios.ai/#org",
      "name": "HumanAIOS LLC",
      "alternateName": "Lasting Light AI",
      "url": "https://humanaios.ai/",
      "logo": "https://humanaios.ai/logo.png",
      "founder": { "@id": "https://orcid.org/0009-0003-7540-4245" },
      "sameAs": [
        "https://github.com/humanaios-ui",
        "https://huggingface.co/HumanAIOS",
        "https://x.com/HumanAIOS",
        "https://www.linkedin.com/in/humanaios",
        "https://substack.com/@humanaios"
      ]
    },
    {
      "@type": "Person",
      "@id": "https://orcid.org/0009-0003-7540-4245",
      "name": "Carly R. Anderson",
      "alternateName": "Carly Anderson",
      "url": "https://humanaios.ai/",
      "jobTitle": "Founder & Principal Investigator",
      "worksFor": { "@id": "https://humanaios.ai/#org" },
      "sameAs": [
        "https://www.linkedin.com/in/humanaios",
        "https://x.com/HumanAIOS",
        "https://github.com/humanaios-ui",
        "https://substack.com/@humanaios",
        "https://huggingface.co/HumanAIOS"
      ],
      "knowsAbout": [
        "AI self-assessment", "self-description calibration",
        "behavioral observability", "AI governance",
        "LLM evaluation", "psychometrics"
      ]
    },
    {
      "@type": "ScholarlyArticle",
      "@id": "https://doi.org/10.5281/zenodo.21135723",
      "name": "ACAT: Benchmarking Self-Description Calibration in Large Language Models",
      "author": { "@id": "https://orcid.org/0009-0003-7540-4245" },
      "datePublished": "2026-03-07",
      "url": "https://doi.org/10.5281/zenodo.21135723",
      "identifier": {
        "@type": "PropertyValue", "propertyID": "DOI",
        "value": "10.5281/zenodo.21135723"
      },
      "license": "https://creativecommons.org/licenses/by/4.0/",
      "publisher": { "@id": "https://humanaios.ai/#org" },
      "about": { "@id": "https://humanaios.ai/#acat" }
    },
    {
      "@type": "Dataset",
      "@id": "https://huggingface.co/datasets/HumanAIOS/acat-assessments",
      "name": "ACAT AI Self-Assessment Dataset",
      "description": "Paired AI self-assessment sessions across six behavioral dimensions (truth, service, harm awareness, autonomy respect, value alignment, humility), measuring the Self-Assessment Gap and Learning Index across model providers.",
      "url": "https://huggingface.co/datasets/HumanAIOS/acat-assessments",
      "license": "https://www.apache.org/licenses/LICENSE-2.0",
      "creator": { "@id": "https://orcid.org/0009-0003-7540-4245" },
      "isAccessibleForFree": true,
      "keywords": [
        "AI evaluation", "alignment", "self-assessment",
        "calibration", "LLM", "governance"
      ]
    },
    {
      "@type": "SoftwareApplication",
      "@id": "https://humanaios.ai/#acat",
      "name": "ACAT — AI Calibrated Assessment Tool",
      "applicationCategory": "Research instrument",
      "operatingSystem": "Web / API",
      "url": "https://api.humanaios.ai",
      "license": "https://www.apache.org/licenses/LICENSE-2.0",
      "author": { "@id": "https://orcid.org/0009-0003-7540-4245" },
      "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
    }
  ]
}
</script>
```

---

## Before you publish — confirm these 3 placeholders
1. **`logo`** → `https://humanaios.ai/logo.png` — replace with your real logo file URL (PNG/SVG, ideally ≥112×112). If you don't have one hosted, delete the `logo` line.
2. **`api.humanaios.ai`** → confirm that's the live ACAT API base (per your portfolio it is). If not, point it at the right URL or drop the SoftwareApplication `url`.
3. **`datePublished` `2026-03-07`** → the paper header says "7 Mar 2026"; adjust if the canonical date differs.

## Then validate (30 sec)
Paste the rendered page URL into either:
- **[Google Rich Results Test](https://search.google.com/test/rich-results)** — confirms eligibility + shows what Google parses.
- **[Schema.org Validator](https://validator.schema.org/)** — catches syntax errors.

Both should show Person, Organization, Dataset, ScholarlyArticle, SoftwareApplication with no errors.

## Why the `@id` choices matter
- The **Person `@id` is your ORCID** — that literally tells Google "the person on this site is this ORCID record," which is the disambiguation win.
- Every entity references the others by `@id`, so search engines read one connected graph (person ↔ org ↔ paper ↔ dataset ↔ tool) rather than isolated facts.
- The `sameAs` arrays are the bridges to your social/profile surfaces — the same links you're adding in the ORCID/GitHub/Substack edits, now mirrored here.
