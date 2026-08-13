# Skill Development Standard — Template & Checklist

**Version:** 1.0  
**Effective:** Week 3 STANDARDIZE phase (2026-07-14)  
**Applies to:** All new skills in `skills/` directory

---

## What is a Skill?

A **skill** is a higher-level workflow that users invoke via natural language triggers (e.g., `/acat-corpus-session`). Skills:
- Orchestrate one or more tools
- Define a step-by-step protocol
- May span multiple sessions or transactions
- Are discoverable and triggerable by users

Skills are **NOT** tools (tools are lower-level Python modules).

---

## Skill Structure

```
skills/
├── <skill_name>/
│   ├── SKILL.md                  ← Required: skill definition
│   ├── README.md                 ← Optional: examples, troubleshooting
│   └── [supporting_files]        ← Optional: templates, data files
└── README.md                      ← Skills directory overview
```

---

## File: `<skill_name>/SKILL.md` (Required)

This is the **skill definition** — everything needed to invoke and execute the skill.

### Structure (6 Required Sections)

```markdown
# <Skill Name> — <One-line purpose>

**Version:** X.Y.Z (Zone: 1/2/3)
**Type:** Assessment tool | Workflow harness | Utility | Reference
**Zone:** 1 (draft) | 2 (ratified) | 3 (live)
**Dependencies:** tool_1, tool_2, /external-skill

---

## Purpose

One paragraph describing what the skill does, why it exists, when to use it.
Link to related artifacts (docs, specs, related skills).

---

## When to invoke

- Use case 1: description
- Use case 2: description
- Use case 3: description

**Trigger phrases:**
- `/skill-name`
- "run skill-name"
- "invoke skill-name workflow"

---

## Workflow: N-Step Protocol

Describe the step-by-step workflow. For each step:

### Step 1: [Title]

Description of what happens in this step.

**Input:** What the user/AI provides
**Actions:** What the skill does
**Output:** What the skill produces
**Example:**

\`\`\`bash
Command or code example
\`\`\`

### Step 2: [Title]

... (repeat for all steps)

---

## Output Artifacts

List what the skill produces:

1. **Artifact 1** (format, location)
   - Description
   - Example

2. **Artifact 2** (format, location)
   - Description
   - Example

---

## Integration Points

How does this skill integrate with the system?

- Tools used: `tools/tool_1.py`, `tools/tool_2.py`
- Skills called: `/other-skill`
- Hooks triggered: Rec 2 session init, Rec 3 P1 reminder
- External dependencies: empirica API, Supabase

---

## Zone Routing

**Current status:** Zone 1 (draft) | Zone 2 (ratified) | Zone 3 (live)

**Before Zone 2:**
- [ ] Skill definition complete (SKILL.md ≥ 80% complete)
- [ ] Trigger phrases documented
- [ ] All steps tested (manual or automated)
- [ ] Dependencies verified available
- [ ] Examples present

**Before Zone 3:**
- [ ] Real-world testing complete (≥2 successful invocations)
- [ ] Documentation + troubleshooting guide
- [ ] Monitoring/health checks defined
- [ ] ACAT assessment completed

---

## Known Limitations

- Limitation 1: description
- Limitation 2: description
- Timeline to fix: Week X

---

## References

- Related docs: [link]
- Related tools: [link]
- Related skills: [link]
- Author: [practice name]
- Updated: [date]
```

### Content Guidelines

**Purpose section:**
- One paragraph (3-4 sentences)
- Why the skill exists (not just what it does)
- When to use it (concrete scenarios)
- Link to related documentation or spec

**When to invoke section:**
- 3-5 concrete use cases
- Trigger phrases (how users find and invoke the skill)
- No more than 5 trigger phrases (too many creates ambiguity)

**Workflow section:**
- One step per section
- Sequential (Step 1 → Step 2 → ...)
- For each step: Input → Actions → Output
- Include at least one code/command example
- Use examples from real workflows, not made-up scenarios

**Output artifacts section:**
- List every file/data structure produced
- Include format (JSON, JSONL, CSV, etc.)
- Location (file path or destination)
- Actual example (truncated if >10 lines)

**Integration points section:**
- What tools does this orchestrate?
- What other skills does it call?
- What hooks does it integrate with?
- What external APIs/systems does it depend on?

**Known limitations section:**
- Be honest about what doesn't work
- When will it be fixed?
- Workarounds (if any)

---

## File: `<skill_name>/README.md` (Optional but Recommended)

For skills with complex workflows, add a README with:

### Contents

1. **Examples**
   - 2-3 full walkthroughs of the skill in action
   - Show expected output
   - Show common variations

2. **Troubleshooting**
   - Common errors + fixes
   - How to validate that the skill worked
   - Who to ask for help

3. **Architecture**
   - High-level diagram of tool orchestration
   - Data flow between steps
   - Dependencies graph

4. **FAQ**
   - Can I modify the output?
   - Can I use this skill with X?
   - How long does it take?

---

## Example: Minimal Skill (Zone 1 Draft)

```markdown
# `/validate-data` — Validate and normalize input data

**Version:** 0.1.0 (Zone 1 draft)
**Type:** Utility
**Dependencies:** `tools/data_validator.py`

---

## Purpose

Accepts messy user input (dict, JSON, CSV), normalizes to canonical form,
validates against schema, and returns structured output. Use when you need
to ensure data quality before passing to downstream processes.

---

## When to invoke

- Preparing data for ACAT corpus submission
- Validating user-provided scores or metadata
- Normalizing input from external sources

**Trigger phrases:**
- `/validate-data`
- "validate this data"
- "check if this data is valid"

---

## Workflow: 3-Step Protocol

### Step 1: Accept User Input

User provides data in any format (dict, JSON string, CSV).

**Input:** `data` (dict or JSON string)
**Actions:**
1. Parse input (detect format: JSON, dict, CSV)
2. Load into memory as dict

**Output:** Parsed dict or error message

**Example:**

\`\`\`json
Input: {"name": "test", "type": "STRING", "value": 123}
Output: Loaded as dict
\`\`\`

### Step 2: Validate Against Schema

Validate that required keys + types match schema.

**Input:** Parsed dict
**Actions:**
1. Check required keys present
2. Check value types match schema
3. Return validation result

**Output:** Validation report (ok + data or error)

**Example:**

\`\`\`json
{
  "ok": true,
  "data": {"name": "test", "type": "string", "value": "123"},
  "errors": []
}
\`\`\`

### Step 3: Normalize + Return

Apply normalization rules (lowercase, trim, type coercion).

**Input:** Validated dict
**Actions:**
1. Apply normalization per schema
2. Return canonical form

**Output:** Canonical data dict

---

## Output Artifacts

1. **Validation report** (dict)
   - Format: JSON
   - Location: Returned in-memory
   - Contains: ok, data, errors

2. **Normalized data** (dict)
   - Format: JSON
   - Ready for downstream processing

---

## Integration Points

- Tools: `tools/data_validator.py`
- Called by: ACAT corpus session skill
- External: None

---

## Zone Routing

**Current:** Zone 1 (draft)

**Before Zone 2:**
- [ ] Validation rules documented
- [ ] Edge cases tested
- [ ] Error messages clear

---

## Known Limitations

- Supports only dicts and JSON (no CSV yet)
- No custom schema support (uses hardcoded schema)

---

## References

- Author: empirica-foundation.carly.empirica-foundation-evaluator
- Updated: 2026-07-14
```

---

## Skill Registration Checklist

Before a skill can be discovered and used:

- [ ] SKILL.md file exists in `skills/<skill_name>/SKILL.md`
- [ ] Purpose documented (one paragraph)
- [ ] Workflow steps clear (N-step protocol)
- [ ] Trigger phrases defined (3-5 phrases)
- [ ] Dependencies listed
- [ ] Output artifacts documented
- [ ] Zone status set (Zone 1/2/3)
- [ ] Skill added to `operations/SKILLS_MANIFEST.md`

---

## Activation (Making Skill Discoverable)

**Zone 1 (Draft):**
- Skill definition complete
- Manual invocation possible
- Not yet registered in skill registry
- Not discoverable via `/` trigger

**Zone 2 (Ratified):**
- Skill registered in skill registry
- Discoverable via trigger phrases
- Auto-triggerable by listeners
- Appears in `/help` or skill browser

**Zone 3 (Live):**
- Production-ready
- Actively monitored
- Part of standard workflows

---

## Quality Gate: Before Zone 2

**Skill readiness score (checklist):**

```
Pass if: 90%+ of requirements met
Then: Skill eligible for Zone 2 registration
Then: Register in skill registry → activate triggers
```

---

## Anti-Patterns (Avoid These)

❌ **Vague workflow steps**
- "Do the thing"
- "Process the data"
- "Check if it's valid"

✅ **Concrete, actionable steps**
- "Validate that all 12 ACAT dimensions are present in the input dict"
- "Normalize scores to 0-100 range, apply floor/ceiling"
- "Return structured dict with keys: ok, data, errors"

---

❌ **Missing examples**
- "The skill generates output"
- "The user will see results"

✅ **Specific examples**
- Shows actual JSON output
- Shows command/code used
- Shows expected vs. error case

---

❌ **Unclear dependencies**
- "Requires tools"
- "Calls other skills"

✅ **Explicit dependencies**
- "Calls `tools/acat_corpus_session.py::ACATCorpusSession.set_p1_scores()`"
- "Calls `/acat-session-health-check` skill to verify readiness"

---

## Documentation Quality Rubric

| Element | Zone 1 | Zone 2 | Zone 3 |
|---------|--------|--------|--------|
| Purpose | Required | Required | Required |
| Trigger phrases | Required | Required + tested | Required + monitored |
| Workflow steps | Outline | Complete + examples | Complete + examples + troubleshooting |
| Output artifacts | Listed | Documented + examples | Documented + validated format |
| Dependencies | Listed | Verified + versions | Verified + health checks |
| Examples | Basic | Real + edge cases | Real + edge cases + best practices |

---

**Template Version:** 1.0  
**Next Review:** Week 4 (SUSTAIN phase)

