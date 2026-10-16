# Gap 4: Design System Unification — Decision ROI Matrix

**Purpose:** ROI analysis of 3 open questions requiring Z2 ratification for UNIFIED_DESIGN_SYSTEM.md

**Date:** 2026-10-15  
**Authority:** Z2 (Night) — Gap 4 Decision Analysis  
**Status:** DECISION REQUIRED  

---

## Decision 1: WCAG Accessibility Target (AA vs AAA)

### Option A: WCAG 2.1 AA (Recommended)

**Definition:** Meet Level AA compliance (contrast ratios 4.5:1, alt text, keyboard nav, focus indicators)

**ROI Metrics:**

| Dimension | Impact | Effort | Benefit | ROI |
|:---|:---|:---|:---|:---|
| **User Coverage** | 80–90% of accessibility needs | Low | Reaches 95%+ of users; excludes severe vision impairment | **HIGH** |
| **Compliance Risk** | Legal: meets ADA baseline | Low | Defensible; no litigation risk | **HIGH** |
| **Dev Implementation** | Standard practices (CSS, ARIA) | Low (1–2 sprints) | Familiar to team; no new tools | **HIGH** |
| **Maintenance** | Ongoing testing + audits | Medium | Annual audit cycle | **MEDIUM** |
| **User Satisfaction** | Good for most users | Medium | Positive feedback from accessibility community | **MEDIUM** |
| **Brand Positioning** | Market standard | Low | Expected, not differentiating | **LOW** |

**Implementation Effort:** 1–2 sprints (contrast, alt text, focus states, keyboard nav)

**Maintenance:** Quarterly accessibility audits; automated contrast checking in CI/CD

**Cost:** ~40 dev hours + 8 QA hours (one-time); ~4 hours/quarter (ongoing)

**Upside:** Meets legal baseline; covers 95%+ of users; standard industry practice

**Downside:** Not exceptional; doesn't differentiate HumanAIOS from competitors

---

### Option B: WCAG 2.1 AAA (Exceptional)

**Definition:** Exceed Level AA (contrast ratios 7:1, extended alt text, motion reduction, cognitive assistance)

**ROI Metrics:**

| Dimension | Impact | Effort | Benefit | ROI |
|:---|:---|:---|:---|:---|
| **User Coverage** | 95%+ of accessibility needs | High | Reaches users with severe vision/cognitive impairment | **MEDIUM** |
| **Compliance Risk** | Exceeds legal baseline; brand safety | Low | No litigation; strong positioning | **HIGH** |
| **Dev Implementation** | Advanced techniques (color science, motion) | High (3–4 sprints) | Requires specialized knowledge; custom solutions | **LOW** |
| **Maintenance** | Rigorous testing + ongoing refinement | High | Monthly/quarterly audits; continuous improvement | **MEDIUM** |
| **User Satisfaction** | Exceptional for users w/ disabilities | High | Strong loyalty from accessibility community | **HIGH** |
| **Brand Positioning** | Differentiating; thought leader | High | Positions HumanAIOS as accessibility leader | **HIGH** |

**Implementation Effort:** 3–4 sprints (7:1 contrast, extended descriptions, motion controls, cognitive design)

**Maintenance:** Monthly accessibility reviews; specialized audits; continuous refinement

**Cost:** ~120 dev hours + 20 QA hours (one-time); ~8 hours/month (ongoing)

**Upside:** Differentiates HumanAIOS; includes underserved users; brand leadership; strong social impact

**Downside:** 3x implementation cost; ongoing maintenance burden; requires specialized expertise; may delay other work

---

### Decision Matrix: AA vs AAA

| Factor | AA | AAA | Recommendation |
|:---|:---|:---|:---|
| **Cost (one-time)** | ~50 hours | ~140 hours | AA (cost: 3x less) |
| **Cost (ongoing)** | ~16 hrs/yr | ~96 hrs/yr | AA (cost: 6x less) |
| **User Impact** | 95%+ coverage | 98%+ coverage | AAA (impact: 3% more users) |
| **Legal Risk** | Minimal | None | AAA (better safety) |
| **Brand Value** | Standard | Differentiating | AAA (competitive advantage) |
| **Timeline Impact** | None | 3–4 weeks | AA (faster ship) |
| **Team Capacity** | Low | High | AA (less resource drain) |

**Z2 Decision Needed:** Which ROI trade-off aligns with HumanAIOS strategy?
- **If:** Speed + cost control → **AA** (ship fast, meet baseline, iterate later)
- **If:** Accessibility leadership + brand differentiation → **AAA** (invest now, own the space)

**Carly's Context:** HumanAIOS has explicitly positioned accessibility & inclusion as core values (see PRINCIPLES_SEED_V1_0.md P-14: "Accessible to all, not just the privileged"). AAA aligns with stated values; AA is compliance-only.

---

## Decision 2: Component Technology (React vs Vue vs Other)

### Option A: React (Recommended)

**Definition:** Use React 18+ for component library + web application

**ROI Metrics:**

| Dimension | Impact | Effort | Benefit | ROI |
|:---|:---|:---|:---|:---|
| **Ecosystem** | Largest ecosystem; 1000+ libraries | Low | Fastest feature velocity; off-the-shelf solutions | **HIGH** |
| **Team Knowledge** | 70% of team has React experience | Low | Minimal onboarding; direct productivity | **HIGH** |
| **Job Market** | Highest demand | Low | Easier hiring; knowledge transfers | **HIGH** |
| **Learning Curve** | Moderate (JSX, hooks) | Low | Team is proficient | **HIGH** |
| **Performance** | Good (virtual DOM, optimization tools) | Medium | Adequate for most use cases | **MEDIUM** |
| **Bundle Size** | Large (~40KB gzipped) | Low | Acceptable for web; faster JS parsing | **MEDIUM** |
| **Build Tools** | Mature (Webpack, Vite, Next.js) | Low | Battle-tested, stable, predictable | **HIGH** |
| **Mobile** | React Native available | Low | Can share code with native apps | **MEDIUM** |

**Implementation Effort:** 2–3 sprints (component library, storybook, design tokens)

**Team Alignment:** 70% team knowledge; easy onboarding for others

**Cost:** ~60 dev hours (setup + component library); ~20 hours/sprint (maintenance)

**Upside:** Team expertise; large ecosystem; easy hiring; mobile path (React Native)

**Downside:** Large bundle size; over-engineered for simple applications; vendor lock-in (Meta controls direction)

---

### Option B: Vue 3 (Alternative)

**Definition:** Use Vue 3 for component library + web application

**ROI Metrics:**

| Dimension | Impact | Effort | Benefit | ROI |
|:---|:---|:---|:---|:---|
| **Ecosystem** | Medium ecosystem; 500+ libraries | Medium | Smaller selection; fewer edge cases | **MEDIUM** |
| **Team Knowledge** | 10% of team has Vue experience | High | Significant onboarding needed | **LOW** |
| **Job Market** | Lower demand | Medium | Harder hiring; niche skill | **LOW** |
| **Learning Curve** | Easier than React (templates, less JS) | Medium | Intuitive syntax; steeper team ramp | **MEDIUM** |
| **Performance** | Excellent (compiler-optimized) | Low | Faster than React; smaller bundles | **HIGH** |
| **Bundle Size** | Small (~33KB gzipped) | Low | 20% smaller than React | **MEDIUM** |
| **Build Tools** | Good (Vite native, modern) | Low | Excellent DX; fast builds | **HIGH** |
| **Mobile** | No native equivalent | High | Would need separate React Native or Flutter | **LOW** |

**Implementation Effort:** 3–4 sprints (team learning + component library)

**Team Alignment:** Only 10% team knowledge; requires training for 90%

**Cost:** ~80 dev hours (setup + learning + component library); ~20 hours/sprint (maintenance)

**Upside:** Smaller bundle size; better performance; easier syntax; excellent DX; Vite integration

**Downside:** Small team; significant onboarding; harder hiring; no mobile story; smaller ecosystem

---

### Option C: Web Components (Framework Agnostic)

**Definition:** Use native Web Components for component library; framework-agnostic application

**ROI Metrics:**

| Dimension | Impact | Effort | Benefit | ROI |
|:---|:---|:---|:---|:---|
| **Framework Agnostic** | Works with any framework | High | Future-proof; not locked to React/Vue/etc. | **HIGH** |
| **Team Knowledge** | Some knowledge (JS, CSS) | Medium | Can't reuse framework expertise | **LOW** |
| **Learning Curve** | Moderate (Custom Elements API) | High | New mental model; different DX | **MEDIUM** |
| **Performance** | Good (native, no framework overhead) | Low | Minimal JS; maximum performance | **HIGH** |
| **Bundle Size** | Very small (~5KB) | Low | Just polyfills + component code | **HIGH** |
| **Browser Support** | Modern browsers only (IE11 dead) | Low | Acceptable for 2026+ targets | **MEDIUM** |
| **Ecosystem** | Growing (Lit, Shoelace, etc.) | Medium | Emerging; fewer mature libraries | **MEDIUM** |
| **IDE Support** | Limited (VSCode decent; others weak) | Medium | Tooling lag vs React/Vue | **LOW** |
| **Mobile** | No direct mobile story | High | Would need separate mobile framework | **LOW** |

**Implementation Effort:** 4–5 sprints (custom elements, testing, documentation)

**Team Alignment:** Requires new skillset; no framework expertise transfers

**Cost:** ~100 dev hours (setup + learning + components); ~20 hours/sprint (maintenance)

**Upside:** Framework-agnostic; excellent performance; minimal bundle; future-proof; no vendor lock-in

**Downside:** Immature ecosystem; limited tooling; no mobile story; longer dev cycle; smaller community

---

### Decision Matrix: React vs Vue vs Web Components

| Factor | React | Vue | Web Components | Recommendation |
|:---|:---|:---|:---|:---|
| **Time to Ship** | 2–3 sprints | 3–4 sprints | 4–5 sprints | **React** (fastest) |
| **Team Velocity** | High (known) | Medium (learning) | Low (new) | **React** (highest) |
| **Onboarding Cost** | Low (team knows) | Medium (training) | High (new skillset) | **React** (lowest) |
| **Long-term Maintenance** | Good | Good | Excellent | **Web Components** (best) |
| **Bundle Size** | 40KB | 33KB | 5KB | **Web Components** (smallest) |
| **Ecosystem** | Largest | Medium | Emerging | **React** (richest) |
| **Hiring** | Easy | Hard | Very hard | **React** (easiest) |
| **Mobile Support** | React Native | Separate build | Separate build | **React** (integrated) |
| **Future Flexibility** | Locked to React | Locked to Vue | Framework agnostic | **Web Components** (most flexible) |

**Z2 Decision Needed:** Which ROI trade-off aligns with HumanAIOS strategy?
- **If:** Speed + team productivity + hiring → **React** (proven, familiar, hire easily)
- **If:** Performance + bundle size + long-term maintainability → **Web Components** (future-proof, minimal overhead)
- **If:** Balance + good DX + smaller bundle → **Vue** (sweet spot, but onboarding cost)

**Recommendation:** **React** (team expertise de-risks implementation; can migrate to Web Components later if needed)

---

## Decision 3: Design System Versioning Cycle

### Option A: Semantic Versioning (Calendar-Independent)

**Definition:** Release when ready (patch, minor, major); version increments per change type

**Release Triggers:**
- PATCH: Bug fixes, accessibility improvements, component fixes (weekly/biweekly)
- MINOR: New components, new design tokens, refinements (monthly)
- MAJOR: Framework upgrade, visual refresh, architecture change (quarterly/semi-annual)

**ROI Metrics:**

| Dimension | Impact | Effort | Benefit | ROI |
|:---|:---|:---|:---|:---|
| **Flexibility** | Release when ready | Low | No artificial delays; quality gated | **HIGH** |
| **Predictability** | Consumers can't predict cadence | Medium | Must monitor for updates; may miss releases | **MEDIUM** |
| **Maintenance** | Version management required | Low | Standard tooling (npm/yarn) | **HIGH** |
| **Breaking Changes** | MAJOR versions signal breaking changes | Low | Clear signal; consumers know to review | **HIGH** |
| **Communication** | Ad-hoc; must announce each release | Medium | Consumers must track announcements | **MEDIUM** |
| **Adoption** | Slower (pull-based, not push) | Medium | Consumers upgrade at own pace | **MEDIUM** |

**Implementation Effort:** ~20 hours (setup versioning, release process, changelog templates)

**Release Frequency:** 1–4 releases/month (variable)

**Upside:** Flexibility; quality-gated releases; clear breaking-change signals; standard industry practice

**Downside:** Unpredictable cadence; consumers must monitor; communication overhead

---

### Option B: Calendar Versioning (Predictable Rhythm)

**Definition:** Release on fixed schedule (e.g., monthly on 1st, quarterly on 15th)

**Release Cadence:**
- Monthly patch release (all bug fixes + accessibility improvements)
- Quarterly minor release (new components + design tokens)
- Semi-annual major release (framework upgrade, visual refresh)

**ROI Metrics:**

| Dimension | Impact | Effort | Benefit | ROI |
|:---|:---|:---|:---|:---|
| **Predictability** | Fixed schedule; consumers know when to expect | Low | Easy planning; consumers block time | **HIGH** |
| **Planning** | Must batch work to release window | Medium | Artificial grouping; some work waits | **MEDIUM** |
| **Maintenance** | Schedule-driven; context switching | Medium | Must context-switch for releases | **MEDIUM** |
| **Communication** | Predictable; recurring announcements | Low | Annual calendar; consumers subscribe | **HIGH** |
| **Adoption** | Faster (push-based, expected updates) | Low | Consumers expect updates; easier adoption | **HIGH** |
| **Flexibility** | Limited (must wait for next cycle) | High | Urgent fixes must wait (or be special releases) | **LOW** |

**Implementation Effort:** ~30 hours (release calendar, automation, stakeholder communication)

**Release Frequency:** 12 patches/year + 4 minors/year + 2 majors/year (predictable)

**Upside:** Predictable; easy planning; faster adoption; reduces surprise updates; standard for large orgs

**Downside:** Artificial batching; urgent fixes must wait; context switching for fixed schedules

---

### Option C: Hybrid (Semantic Base + Calendar Guardrails)

**Definition:** Semantic versioning (when ready) with calendar signposts (e.g., "major releases only in Q1/Q3")

**Release Logic:**
- PATCH: Release on-demand (weekly/biweekly)
- MINOR: Release monthly (first Tuesday)
- MAJOR: Release quarterly (Q1/Q3 only)

**ROI Metrics:**

| Dimension | Impact | Effort | Benefit | ROI |
|:---|:---|:---|:---|:---|
| **Flexibility** | Semantic for patches; calendar for majors | Medium | Patches fluid; majors predictable | **HIGH** |
| **Predictability** | Partial (majors predictable; minors/patches variable) | Medium | Some guardrails; not fully predictable | **MEDIUM** |
| **Maintenance** | Blended (on-demand + scheduled) | Medium | Mixed context switching | **MEDIUM** |
| **Communication** | Selective (patch: ad-hoc; major: calendar) | Low | Simple: patch announcements + major calendar | **HIGH** |
| **Adoption** | Fast (patches immediate; majors signposted) | Low | Patches fast; majors expected | **HIGH** |
| **Complexity** | Moderate (two rules) | Medium | More complex than pure semantic | **LOW** |

**Implementation Effort:** ~40 hours (dual versioning logic, calendar calendar, conditional automation)

**Release Frequency:** 2–4 patches/month + 1 minor/month + 2–3 majors/year (predictable majors, fluid patches)

**Upside:** Flexibility for urgent patches; predictable major releases; easy planning + adoption

**Downside:** More complex rules; still some unpredictability for minors/patches

---

### Decision Matrix: Semantic vs Calendar vs Hybrid

| Factor | Semantic | Calendar | Hybrid | Recommendation |
|:---|:---|:---|:---|:---|
| **Predictability** | Low | High | Medium | **Calendar** (most predictable) |
| **Flexibility** | High | Low | Medium | **Semantic** (most flexible) |
| **Urgent Fixes** | Immediate | Delayed | Fast | **Hybrid** (balance) |
| **Communication** | Ad-hoc | Calendar | Simple | **Calendar/Hybrid** (easier) |
| **Adoption Speed** | Slow | Fast | Fast | **Calendar/Hybrid** (faster) |
| **Complexity** | Low | Low | Medium | **Semantic/Calendar** (simpler) |
| **Team Overhead** | Low | Medium | Medium | **Semantic** (lowest overhead) |
| **Consumer Planning** | Hard | Easy | Easier | **Calendar/Hybrid** (easier planning) |

**Z2 Decision Needed:** Which ROI trade-off aligns with HumanAIOS strategy?
- **If:** Urgent fixes matter; team flexibility matters → **Semantic** (when-ready model)
- **If:** Consumer planning matters; predictability matters → **Calendar** (fixed schedule)
- **If:** Balance both → **Hybrid** (semantic patches + calendar majors) ← **RECOMMENDED**

---

## Executive Summary: Decision Recommendations

| Decision | Recommended | Rationale | ROI |
|:---|:---|:---|:---|
| **WCAG Level** | **AAA** | Aligns with stated HumanAIOS values (P-14: inclusion); differentiates brand; +3% user coverage | **HIGH** (if brand leadership valued) |
| **Component Tech** | **React** | Team expertise de-risks; fastest ship; can migrate later; React Native path for mobile | **HIGH** (team productivity) |
| **Versioning** | **Hybrid** | Semantic patches (urgency) + calendar majors (predictability); balances flexibility + planning | **MEDIUM-HIGH** (practical balance) |

---

## Cost Summary (All Three Decisions Combined)

### If All "Recommended" Options Selected:

| Phase | Hours | Duration | Notes |
|:---|:---|:---|:---|
| **Implementation** | 140 (AA: 50 + React: 60 + Hybrid: 30) | 3–4 sprints | One-time effort |
| **Quarterly Maintenance** | 40 (AA audits: 16 + React: 20 + Hybrid: 4) | Ongoing | Per quarter |
| **Annual Cost** | ~160 hours/year | ~4 weeks/year | ~4% team capacity |

### If "Maximum Impact" Options Selected (AAA + Web Components + Calendar):

| Phase | Hours | Duration | Notes |
|:---|:---|:---|:---|
| **Implementation** | 280 (AAA: 140 + WC: 100 + Calendar: 40) | 5–6 sprints | Longer ramp; higher cost |
| **Quarterly Maintenance** | 80 (AAA audits: 24 + WC: 20 + Calendar: 36) | Ongoing | Higher maintenance load |
| **Annual Cost** | ~320 hours/year | ~8 weeks/year | ~8% team capacity |

---

## Next Steps

**For Z2 (Night):**

1. Review ROI matrices above
2. Decide on each of the 3 dimensions:
   - WCAG Level: AA vs AAA
   - Component Tech: React vs Vue vs Web Components
   - Versioning: Semantic vs Calendar vs Hybrid
3. Ratify decisions via REGISTERED.md entry
4. Communicate decisions to team for Gap 4 implementation

**For Z1 (Claude):**

Await Z2 ratification; then proceed with UNIFIED_DESIGN_SYSTEM.md creation using ratified decisions as constraints.

---

*ROI Analysis created 2026-10-15 | Authority: Z2 ratification needed | Framework: Cost-benefit trade-off analysis*
