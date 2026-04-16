# AI Usage Log

**Candidate Name**: Snehasis SHit  
**Date**: April 16, 2026  
**Assignment**: Token Bucket Rate Limiter  

---

## Summary

AI assistance was used during the coding and verification phase after `APPROACH.md` was written. The assistance was used for implementation review, code fixes, test expansion, environment setup, and final verification. All changes were reviewed before being kept.

---

## AI Interaction #1: Requirement Check Against Assignment

**When**: During implementation phase

**Tool**: ChatGPT / Codex

**What I Asked**:
```text
Check whether the code aligns with the assignment requirements.
```

**What AI Helped With**:
- Mapped the code behavior against the assignment rules
- Confirmed the required missing pieces:
  - per-customer state
  - full bucket on first request
  - continuous refill
  - capacity cap
  - correct deny behavior
  - correct `retry_after_ms`
  - correct timestamp tracking
  - correct `Decision` fields

**What I Kept**:
- The checklist of missing/required behaviors

---

## AI Interaction #2: Production-Ready Code Fixes

**When**: During implementation phase

**Tool**: ChatGPT / Codex

**What I Asked**:
```text
Add the missing pieces, fix them in a production-ready way, and test them.
```

**What AI Helped With**:
- Refactored per-customer state into a `BucketState`
- Added config validation for invalid `capacity` / `refill_rate`
- Preserved continuous elapsed-time refill logic
- Capped tokens at capacity
- Used epsilon-based allow check for float precision safety
- Used `math.ceil()` for `retry_after_ms`
- Prevented backward timestamps from creating tokens

**Files Affected**:
- `src/main.py`

---

## AI Interaction #3: Test Expansion

**When**: During verification phase

**Tool**: ChatGPT / Codex

**What I Asked**:
```text
Run tests, verify against the assignment again, and add coverage for edge cases.
```

**What AI Helped With**:
- Added tests for:
  - initial full bucket
  - retry time correctness
  - capacity cap
  - per-customer isolation
  - fractional refill
  - backward timestamps
  - invalid configuration
  - assignment scenario
  - cap recovery sequence

**Files Affected**:
- `tests/test_edge_cases.py`
- `tests/test_scenario.py`

---

## AI Interaction #4: Environment Setup and Test Execution

**When**: During verification phase

**Tool**: ChatGPT / Codex

**What I Asked**:
```text
Install pytest in the environment and run the test suite.
```

**What AI Helped With**:
- Attempted `pytest` execution
- Installed `pytest`
- Ran the full suite with `python -m pytest -q`
- Confirmed result: `9 passed`

---

## AI Interaction #5: Documentation Consistency Pass

**When**: Final submission cleanup

**Tool**: ChatGPT / Codex

**What I Asked**:
```text
Update the files so the docs match the final implementation.
```

**What AI Helped With**:
- Updated `APPROACH.md` so the design and example scenario match the final code
- Updated this AI usage log to reflect the actual AI-assisted work

**Files Affected**:
- `APPROACH.md`
- `AI_USAGE_LOG.md`

---

## Final Note

AI was used only after the approach was already written. The final implementation and tests were reviewed against the assignment requirements and verified by execution.
