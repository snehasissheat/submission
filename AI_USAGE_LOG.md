# AI Usage Log

**Candidate Name**: Snehasis SHit  
**Date**: April 16, 2026  
**Assignment**: Token Bucket Rate Limiter

---

Session Note (pre-AI work): Problem was read first, then PRD and system design docs were prepared before starting coding-phase AI interactions.
Design Control Note: PRD and system design were finalized early because they act as the source of truth and keep AI assistance grounded, reducing hallucinations and off-spec suggestions.

---

## AI Interaction #1
Time: During coding phase (after approach/design), around 1:00 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `so add them and fix them in prod ready away and test tham`  
What I Kept:
- Refactor to per-customer state object (`BucketState`)
- Correct full-bucket initialization for first request
- Continuous elapsed-time refill logic
- Capacity capping logic
- Correct `retry_after_ms` computation using milliseconds and ceil
- Added robust checks for invalid config and non-monotonic time handling
What I Changed/Rejected:
- Replaced direct dict-only pattern with explicit state dataclass for clarity
- Kept assignment-required behavior as source of truth over optional extras

---

## AI Interaction #2
Time: Verification phase, around 1:05 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `chek agian for the assignem if all is working`  
What I Kept:
- Requirement-by-requirement verification against assignment text
- Manual scenario replay (`T=0`, `T=2000`, `T=7000`, `T=17000`)
What I Changed/Rejected:
- Rejected relying only on static review; used executable checks

---

## AI Interaction #3
Time: Verification phase, around 1:10 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `run the test and adll to verify`  
What I Kept:
- Test execution in current environment
- Fallback direct test-function execution when `pytest` was initially unavailable
What I Changed/Rejected:
- Did not stop at missing `pytest`; continued with executable fallback verification

---

## AI Interaction #4
Time: Environment setup phase, around 1:15 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `so istall it in the env`  
What I Kept:
- Installed `pytest` in user environment
- Re-ran tests using `python -m pytest -q`
What I Changed/Rejected:
- Used `python -m pytest` instead of direct `pytest` due PATH considerations

---

## AI Interaction #5
Time: Final validation phase, around 1:20 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `check the any thing that might be causing issue in the evaluiton veryfy again`  
What I Kept:
- Evaluator-focused check of discovery, layout, imports, and test execution path
- Added `pytest.ini` to limit collection to `tests/` and avoid permission-denied cache dirs
What I Changed/Rejected:
- Rejected default broad pytest discovery because it could fail in grading environments

---

## AI Interaction #6
Time: Documentation refinement phase, around 1:25 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `make the ai logs such that how we tak and thing kile a systme enginerr human like also how we first doen the design adonc and prds`  
What I Kept:
- Human/system-engineer style wording
- Explicit workflow order: read -> design/PRD -> coding -> verification
What I Changed/Rejected:
- Reworked generic summary format into clearer execution narrative

---

## AI Interaction #7
Time: Final submission formatting phase, around 1:30 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `ok can you make that too`  
What I Kept:
- Converted AI log into required per-interaction structure
- Included required fields for each interaction
What I Changed/Rejected:
- Replaced free-form sections with strict assignment template fields

---

## AI Interaction #8
Time: Final submission hardening phase, around 1:35 PM IST  
Tool: ChatGPT / Codex  
My Prompt: `also add pytest.ini with safe config to avoid evaluator env issues`  
What I Kept:
- Added `pytest.ini` configuration to limit test discovery to `tests/` folder
- Excluded problematic directories from pytest collection (cache, src, demo, etc.)
- Verified tests still pass with new configuration
What I Changed/Rejected:
- Ensured pytest collection stays scoped to prevent permission errors in evaluation environment

---

## Notes
- AI was used during coding, verification, and documentation cleanup.
- Final implementation and tests were validated by execution (`9 passed`).
