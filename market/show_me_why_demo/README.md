# Show Me Why Demo Scaffold

**Status:** Prototype scaffold  
**Sensitivity rule:** Non-sensitive fixtures only  
**Validation gate:** A demo walkthrough is not sufficient for differentiation; it is required but subordinate to external-user testing.

## Minimal view contract

A valid demo must expose exactly these sections for one consequential action:

1. `CLAIM`
2. `STATUS`
3. `EVIDENCE`
4. `WARRANT`
5. `AUTHORITY`
6. `ROLE`
7. `CHALLENGES`
8. `UNCERTAINTY`
9. `ACTION`
10. `RECEIPT`
11. `CONSEQUENCE`

## Initial fixture

- **Fixture ID:** `DEMO-FIXTURE-0001`
- **Scenario:** Non-sensitive repository change proposal reviewed through claim → evidence → warrant → authority → action → receipt.
- **Purpose:** Check whether a reviewer can navigate the chain without needing a narrative explanation.

## Test checklist

- [x] The scaffold names the required sections.
- [x] The scaffold uses a non-sensitive fixture class.
- [x] The scaffold explicitly shows uncertainty and challenge state.
- [ ] An external user has completed the walkthrough.
- [ ] Comparative comprehension has been measured against an ordinary explanation.

## Current interpretation

The scaffold exists and can be smoke-tested internally, but issue #499 remains **UNPROVEN** for public utility until an external user completes the walkthrough under pre-registered criteria.
