# AI Usage Log

**Candidate Name**: Snehasis SHit  
**Date**: April 16, 2026  
**Assignment**: Token Bucket Rate Limiter

---

## Pre-Coding Phase

- Read the full assignment prompt first.
- Completed initial approach notes before implementation.
- Used limited AI assistance to structure PRD/design writeups so requirements were organized in a compact, consistent format.

Design Control Note: PRD and design were prepared early as source-of-truth artifacts to keep implementation on-spec, reduce ambiguity, and keep context compact.

---

## AI Interaction #1
Time: During documentation phase, around 12:45 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `Help me structure PRD and design docs in a concise system-engineering format so requirements are clear and compact.`  
What I Kept:
- Structured sections for objective, requirements, data model, algorithm, and verification
- Compact, scannable format for faster implementation reference
What I Changed/Rejected:
- Kept all technical decisions aligned to assignment constraints; removed any generic sections not useful for this problem

---

## AI Interaction #2
Time: During coding phase (after design/approach completion), around 1:00 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `Review the current token-bucket implementation against assignment requirements and list missing or risky behaviors.`  
What I Kept:
- Requirement gap checklist:
  - per-customer state
  - full initialization on first request
  - elapsed-time refill
  - capacity cap
  - correct denial behavior
  - correct `retry_after_ms`
What I Changed/Rejected:
- Converted checklist into concrete implementation tasks before editing code.

---

## AI Interaction #3
Time: During implementation phase, around 1:05 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `Apply production-ready fixes for the identified gaps and add validation/edge-case handling.`  
What I Kept:
- `BucketState`-based per-customer model
- Input validation for invalid `capacity` / `refill_rate`
- Millisecond retry calculation using `ceil`
- Defensive handling for non-monotonic timestamps
What I Changed/Rejected:
- Kept only behavior aligned with assignment contract; avoided adding unrelated features.

---

## AI Interaction #4
Time: During verification phase, around 1:10 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `Run and extend tests for assignment scenario plus critical edge cases.`  
What I Kept:
- Expanded tests for scenario and edge behavior
- Verification of per-customer isolation and fractional refill timing
What I Changed/Rejected:
- Rejected shallow verification; required executable test evidence.

---

## AI Interaction #5
Time: Environment setup phase, around 1:15 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `Install pytest in the environment and execute the suite.`  
What I Kept:
- `pytest` installation
- Test execution via `python -m pytest -q`
What I Changed/Rejected:
- Used module invocation (`python -m pytest`) instead of direct `pytest` binary to avoid PATH issues.

---

## AI Interaction #6
Time: Evaluation-readiness phase, around 1:20 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `Check for grading risks (test discovery, file layout, import behavior) and harden submission reliability.`  
What I Kept:
- Added [pytest.ini](C:/Users/Admin/Submissions/submission/pytest.ini) to constrain discovery to `tests/`
- Re-ran full suite from repo root
What I Changed/Rejected:
- Rejected default broad discovery because it could collect restricted cache/temp folders in this environment.

---

## AI Interaction #7
Time: Documentation consistency phase, around 1:25 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `Align documentation with final implementation and test outcomes.`  
What I Kept:
- Updated docs to match final code semantics (`BucketState`, `ceil` retry logic, 9 passing tests)
What I Changed/Rejected:
- Removed stale references to older dict-only model and outdated test counts.

---

## AI Interaction #8
Time: Final submission formatting phase, around 1:30 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `Format AI usage log in strict evaluator template for each interaction.`  
What I Kept:
- Per-interaction structure with required fields:
  - `Time`
  - `Tool`
  - `My Prompt`
  - `What I Kept`
  - `What I Changed/Rejected`
What I Changed/Rejected:
- Replaced earlier narrative-only format with strict template format for compliance.

---

## Final Note

- AI was used for PRD/design structuring, coding, verification, and documentation cleanup.
- Final code behavior was verified by execution (`9 passed`).
