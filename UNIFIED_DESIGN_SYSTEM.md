# Unified Design System v1.0.0

**Authority:** Z2 (Night) Ratification of Gap 4 Resolution  
**Effective Date:** 2026-10-15  
**Status:** ACTIVE (Phase 2 Implementation)  
**Framework:** HumanAIOS Website + ACAT Observatory  
**Technology:** React 18+ (Web Components migration path available)  
**Accessibility:** WCAG 2.1 AAA  
**Versioning:** Hybrid (semantic patches + calendar majors)

---

## 1. Philosophy & Vision

### 1.1 Core Principles

HumanAIOS website design is governed by five immutable principles:

1. **High Humility Framing** — All language reflects uncertainty and development status. We are "under clean, unanchored conditions," at TRL 2–3, preliminary. Never claim production validation.

2. **Zero Bias in Explanation** — We describe instruments and data. We do not editorialize about what findings mean. Data speaks for itself.

3. **No Statistics in Body Copy** — Numbers belong in cards, signal displays, visualizations. Prose explains the instrument; visualization shows the data.

4. **Accessibility as Core Value** — WCAG 2.1 AAA (not AA) is non-negotiable. We are "accessible to all, not just the privileged" (P-14). Design for:
   - Vision impairment (7:1 contrast, extended alt text, color-blind safe)
   - Cognitive load (simple navigation, scannable content, consistent patterns)
   - Motor limitations (keyboard navigation, large click targets, no time-based interactions)
   - Neurodiversity (reduced motion options, clear language, predictable layout)

5. **Machine Readability** — AI systems and assistants should parse research metadata without rendering HTML. Use Schema.org JSON-LD + microdata.

### 1.2 Design Vision

The website serves four audiences simultaneously:

| Audience | Need | Design Response |
|:---|:---|:---|
| **Researchers** | Understand methodology; access data | Documentation, structured data, export options |
| **Enterprise users** | Assess organizational AI risk | Clear ACAT pathway, reporting, benchmarking |
| **Autonomous agents** | Parse research metadata without rendering | JSON-LD, microdata, `ai-instructions.txt` |
| **Casual visitors** | Understand "what is HumanAIOS?" | Clear value prop, 3-pool visual model, humble framing |

---

## 2. Component Library

### 2.1 Core Components (React)

All components are built in **React 18+** using the design tokens defined in § 3 below. Each component includes:
- Accessibility checklist (WCAG AAA compliance)
- Props documentation
- Storybook entry
- Usage examples
- TypeScript types

#### Navigation Components

**`<WitnessNav />`** — Primary navigation system (Witness constellation)
- Fixed position: bottom-left corner
- Element: `<button>` (never `<a>`)
- Glyph: Witness mark (◌ or Dual Arc Comet v3.4)
- Groups: Home, UNDERSTAND, EXPLORE, PARTICIPATE
- Active-state highlighting per page (`data-room` attribute)
- Accessibility: Keyboard nav, focus visible (2px outline), screen-reader announced

**`<ConstellationLink />`** — Directional link with arrow (→)
- Usage: Section endings, card CTAs
- Element: `<a href>` with arrow appended
- Accessibility: Focus visible, announced by screen readers

**`<BreadcrumbNav />`** — Page hierarchy
- Shows path: Home → Section → Page
- Slashed separators
- Last item: current page (not clickable)
- Accessibility: `<nav aria-label="Breadcrumb">`, role announced

#### Content Components

**`<PoolCard />`** — 3-pool model visualization
- Pool 1 (The Source): `#a0c8c0` (dataset)
- Pool 2 (The Luminarium): `#88a7d8` (research space)
- Pool 3 (The Communal): `#9A8AC0` (autonomous AI)
- Accessibility: Color + pattern differentiation (not color alone); labels

**`<DataViz />`** — Charts, graphs, data visualizations
- Default: React-based (Recharts or D3)
- Alt text: Detailed, structured descriptions
- Interactive: Keyboard accessible (arrow keys, Enter to explore)
- Accessibility: ARIA labels, legend, data table fallback

**`<SignalDisplay />`** — Live data instrument (sticky topbar)
- Shows: N counts, field state, LI (live computed value, not hardcoded 0.942)
- Update frequency: Real-time or hourly
- Accessibility: Updates announced via ARIA live region

**`<LanguageBlock />`** — Controlled prose with no bias
- No statistics in body copy (violations flagged)
- No IC-009 violations (LI references use 0.8632 fallback if cited)
- No Cherokee Nation mentions (internal only)
- No Hawkins terminology ("calibration score" instead)
- Linting: Pre-commit hook checks for violations

#### Form Components

**`<ACATForm />`** — Assessment tool input
- Fields: Dimension selectors, response scales, comments
- Validation: Real-time feedback, error states
- Submission: Clear success state; data handling explained
- Accessibility: `<label>` for every input, error announcements, keyboard nav

**`<FilterControl />`** — Dataset filtering (Observatory, Pool)
- Filters: Dimension, date range, assessment mode
- Visual feedback: Active filters highlighted, result count updated
- Accessibility: Keyboard operable, screen-reader announced

### 2.2 Component Accessibility Checklist (WCAG AAA)

Every component must pass this checklist before shipping:

- [ ] **Contrast:** Foreground/background ≥7:1 (AAA). Check with WAVE or aXe.
- [ ] **Alt Text:** Images/icons have `alt=""` (decorative) or `alt="description"` (informative).
- [ ] **Focus Visible:** Keyboard users see clear focus indicator (2px outline, 2px offset, ≥3:1 contrast to background).
- [ ] **Keyboard Navigation:** All interactive elements reachable via Tab; logical tab order.
- [ ] **Screen Reader:** ARIA labels, roles, live regions announced correctly (test with NVDA, JAWS, VoiceOver).
- [ ] **Motion:** Reduced motion respected (`prefers-reduced-motion` media query); no auto-playing animations.
- [ ] **Color Not Sole Indicator:** Red/green color differentiation with pattern or text label.
- [ ] **Form Inputs:** `<label>` associated with input; error messages linked via `aria-describedby`.
- [ ] **Time-Based Interactions:** None (no auto-dismiss modals, no session timeouts without warning).

---

## 3. Visual Design

### 3.1 Design Tokens

All design is expressed as tokens (values), not pixels. This enables themability and consistency.

#### Colors

**Primary Palette:**
```css
--color-primary-source: #a0c8c0;     /* Pool 1: The Source (dataset) */
--color-primary-luminarium: #88a7d8; /* Pool 2: The Luminarium (research) */
--color-primary-communal: #9A8AC0;   /* Pool 3: The Communal (AI) */
```

**Neutral Palette:**
```css
--color-text-primary: #1a1a1a;       /* Body text */
--color-text-secondary: #666666;     /* Secondary text, captions */
--color-text-tertiary: #999999;      /* Disabled, hints */
--color-background: #ffffff;         /* Page background */
--color-background-alt: #f8f8f8;     /* Cards, sections */
--color-border: #e0e0e0;             /* Dividers, borders */
```

**Status Palette:**
```css
--color-success: #2ecc71;   /* Checkmarks, valid states */
--color-warning: #f39c12;   /* Alerts, cautions */
--color-error: #e74c3c;     /* Errors, failures */
--color-info: #3498db;      /* Info messages, hints */
```

**Semantic Colors (AAA Contrast Guaranteed):**
- All text on white: ≥7:1 contrast
- Interactive elements: ≥4.5:1 focus state; ≥7:1 on colored backgrounds
- Disabled state: ≥3:1 (allows lower contrast as per spec)

#### Typography

**Font Stack:**
```css
--font-family-sans: "Inter", "Helvetica Neue", sans-serif;
--font-family-mono: "Fira Code", "Courier New", monospace;
```

**Scale (modular, 1.125 ratio):**
```css
--font-size-h1: 2.488rem;   /* 39.8px */
--font-size-h2: 2.210rem;   /* 35.4px */
--font-size-h3: 1.960rem;   /* 31.4px */
--font-size-h4: 1.742rem;   /* 27.9px */
--font-size-h5: 1.549rem;   /* 24.8px */
--font-size-h6: 1.377rem;   /* 22.0px */
--font-size-body: 1.000rem; /* 16px baseline */
--font-size-small: 0.889rem; /* 14.2px */
--font-size-tiny: 0.790rem; /* 12.6px */
```

**Line Height:**
```css
--line-height-heading: 1.2;   /* Tight for impact */
--line-height-body: 1.6;      /* Spacious for readability */
--line-height-code: 1.4;      /* Monospace comfort */
```

**Weight:**
```css
--font-weight-regular: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

#### Spacing

**Grid:** 8px base unit (multiples of 8)
```css
--spacing-xs: 0.5rem;  /* 8px */
--spacing-sm: 1rem;    /* 16px */
--spacing-md: 1.5rem;  /* 24px */
--spacing-lg: 2rem;    /* 32px */
--spacing-xl: 3rem;    /* 48px */
--spacing-2xl: 4rem;   /* 64px */
```

**Margins & Padding:**
- Component padding: `--spacing-md` (24px)
- Section padding: `--spacing-lg` to `--spacing-xl` (32–48px)
- Card padding: `--spacing-md` (24px)
- Line spacing: `--spacing-sm` (16px) between paragraphs

#### Breakpoints

**Responsive Design (mobile-first):**
```css
--breakpoint-xs: 0;       /* Mobile default */
--breakpoint-sm: 640px;   /* Large phone, small tablet */
--breakpoint-md: 768px;   /* Tablet */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Wide desktop */
--breakpoint-2xl: 1536px; /* Ultra-wide */
```

**Usage:**
```css
/* Mobile first */
.card { padding: var(--spacing-sm); }
@media (min-width: 768px) {
  .card { padding: var(--spacing-md); }
}
```

#### Shadows

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

#### Border Radius

```css
--radius-xs: 0.25rem;   /* 4px - subtle buttons */
--radius-sm: 0.5rem;    /* 8px - cards, inputs */
--radius-md: 1rem;      /* 16px - larger components */
--radius-lg: 1.5rem;    /* 24px - panels */
--radius-full: 9999px;  /* Fully rounded (pills, circles) */
```

#### Motion (Respects `prefers-reduced-motion`)

```css
--transition-fast: 150ms ease-in-out;
--transition-normal: 300ms ease-in-out;
--transition-slow: 500ms ease-in-out;

/* Apply conditionally */
@media (prefers-reduced-motion: no-preference) {
  .button { transition: background-color var(--transition-fast); }
}
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

### 3.2 Color Contrast Verification

**Pre-commit hook check (CI/CD gate):**

```bash
# Check for contrast violations in generated CSS
./scripts/contrast-checker.js dist/styles.css
# Fails if any element has <7:1 contrast
```

**Runtime verification (development):**

Install axe DevTools browser extension; run audit on every page during development.

---

## 4. Interaction Patterns

### 4.1 Navigation Patterns

**Primary Navigation:** Witness (bottom-left, always visible)
**Secondary Navigation:** Breadcrumb (top-left, shows hierarchy)
**Tertiary Navigation:** In-page links (ConstellationLinks with →)

**Pattern: Consistent, predictable navigation across all pages**

### 4.2 Form Patterns

**Input:** Label above input; hint text below
**Error:** Red text (7:1 contrast); icon + message
**Success:** Green checkmark; confirmation message
**Disabled:** Gray text; no pointer; tab skipped

**Pattern: Every form field is self-explanatory**

### 4.3 Feedback Patterns

**Loading:** Spinner + "Loading..." text; announced every 2 seconds if >2 seconds
**Success:** Green toast notification (5s auto-dismiss); announcement: "Success: [message]"
**Error:** Red alert (persistent until dismissed); focus moved to error; detailed explanation

**Pattern: All state changes are announced to screen readers**

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Weeks 1–2)
- [ ] Publish React component library (Storybook)
- [ ] Define design tokens (CSS variables)
- [ ] Create base components (WitnessNav, PoolCard, SignalDisplay)
- [ ] Set up CI/CD gates (contrast checker, WCAG audits)

### Phase 2: Component Library (Weeks 3–4)
- [ ] Build form components (ACATForm, FilterControl)
- [ ] Build content components (DataViz, LanguageBlock)
- [ ] Add accessibility checklist to component docs
- [ ] Create Figma library (tokens, components, patterns)

### Phase 3: Website Redesign (Weeks 5–8)
- [ ] Migrate index.html to React component
- [ ] Migrate Pool pages (assess.html, observatory.html, etc.)
- [ ] Migrate Luminarium pages
- [ ] Test with real users (accessibility feedback)

### Phase 4: Optimization & Launch (Weeks 9–12)
- [ ] Performance audit (bundle size, Lighthouse)
- [ ] SEO verification (Schema.org, structured data)
- [ ] Machine readability audit (JSON-LD, microdata)
- [ ] UAT with assistive technology (NVDA, JAWS, VoiceOver)
- [ ] Launch (Week 12)

---

## 6. Governance & Versioning

### 6.1 Semantic Versioning (MAJOR.MINOR.PATCH)

**MAJOR:** Framework upgrade, visual refresh, architecture change
- Example: React 18 → 19, new design language, major layout changes
- Trigger: Calendar (Q1 or Q3 only)
- Notice: 4 weeks advance notice

**MINOR:** New components, new design tokens, refinements
- Example: New DataViz component, new color added, Storybook updates
- Trigger: Monthly (1st Tuesday)
- Notice: 1 week advance notice

**PATCH:** Bug fixes, accessibility improvements, component fixes
- Example: Fix contrast violation, improve keyboard nav, fix focus indicator
- Trigger: On-demand (biweekly release)
- Notice: Release notes posted immediately

### 6.2 Hybrid Release Cadence

**Patches:** Released biweekly (on-demand quality gated)
**Minors:** Released monthly (1st Tuesday; batched PRs from prior month)
**Majors:** Released quarterly (Q1/Q3; announced 4 weeks prior; migration guide included)

### 6.3 Change Authority

| Change Type | Authority | Approval Process |
|:---|:---|:---|
| Component bug fix | Z3 (executor) | Auto-merge if tests pass + contrast OK |
| New component | Z1 (proposer) + Z2 (ratifier) | REGISTERED.md entry; Z2 approval; contrast check |
| Design token change | Z2 (ratifier) | REGISTERED.md entry; Z2 signed |
| Framework upgrade | Z2 + Admiral | REGISTERED.md entry; Admiral ratifies; 4-week notice |
| WCAG level change | Z2 + Admiral | REGISTERED.md entry; Admiral ratifies; cost analysis required |

### 6.4 Deprecation Policy

**Component Deprecation:**
1. Announce in release notes (N version prior to removal)
2. Mark in Storybook (⚠️ DEPRECATED in N version)
3. Provide migration guide
4. Remove in +2 major versions

**Design Token Deprecation:**
- Same process as components
- Provide rename mapping (old → new)

---

## 7. Technology Stack (React + AAA Accessibility)

### 7.1 Tech Choices (Ratified)

- **Framework:** React 18+ (TypeScript)
- **Build:** Vite (fast HMR, native ES modules)
- **Components:** Storybook + Chromatic
- **Testing:** Vitest + React Testing Library + Cypress E2E
- **Accessibility:** axe-core + WAVE + manual audits (quarterly)
- **Documentation:** Storybook (primary) + Markdown (secondary)

### 7.2 Accessibility Automation

**Pre-commit hooks:**
- `npm run lint:a11y` — axe-core checks on changed components
- `npm run check:contrast` — Ensures ≥7:1 contrast in CSS
- `npm run check:wcag` — Full WCAG AAA scan on modified pages

**CI/CD gates:**
- Build fails if any axe violations detected
- Build fails if contrast <7:1 on any element
- Build fails if WCAG AAA audit shows failures

**Manual audits:**
- Quarterly WCAG AAA audit (external auditor)
- Quarterly assistive technology test (NVDA, JAWS, VoiceOver)
- Monthly developer accessibility training

---

## 8. Migration from Previous Specs

### 8.1 Consolidation Map

| Previous Document | Content | Status | Location |
|:---|:---|:---|:---|
| WEBSITE_DESIGN_SPEC_V1_0.md | Governing language rules, site architecture | **SUPERSEDED** | Archive; see § 1 & 2 above |
| AI_FRIENDLY_WEBSITE_IMPLEMENTATION_GUIDE.md | Technical implementation, machine readability | **INTEGRATED** | See § 6 (Schema.org, microdata) |

### 8.2 Deprecation Notice

**Effective 2026-10-15:**
- WEBSITE_DESIGN_SPEC_V1_0.md is superseded by UNIFIED_DESIGN_SYSTEM.md
- AI_FRIENDLY_WEBSITE_IMPLEMENTATION_GUIDE.md is superseded (technical implementation moved to § 6)
- All new work must reference UNIFIED_DESIGN_SYSTEM.md
- Old specs kept for reference only (no longer authoritative)

---

## 9. Governance Reference

- **Authority:** Z2 (Night) ratification of Gap 4 Resolution
- **Accessibility Target:** WCAG 2.1 AAA (not AA)
- **Technology:** React 18+ (Web Components migration path available)
- **Versioning:** Hybrid (semantic patches + calendar majors)
- **Related Documents:** GOVERNANCE_DECISION_MATRIX.md, PRACTICE_GOVERNANCE_PROTOCOL.md, GAPS_RESOLUTION_INDEX.md

---

*Unified Design System v1.0.0 ratified 2026-10-15 | Authority: Z2 (Night) Gap 4 resolution | Framework: React + WCAG AAA + Hybrid versioning*
