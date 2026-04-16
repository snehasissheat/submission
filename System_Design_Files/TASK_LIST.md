# Task List

**Project**: Token Bucket Rate Limiter  
**Date**: April 16, 2026  
**Status**: Completed

---

## Phase 1: Problem Intake and Planning

- [x] Read and analyze full assignment prompt
- [x] Identify mandatory submission structure and constraints
- [x] Note deliberate errors in prompt for documentation
- [x] Prepare approach/design direction before implementation

---

## Phase 2: System Design Artifacts

- [x] Draft PRD with requirements and acceptance scenario
- [x] Draft system design with runtime flow and data model
- [x] Align design to token bucket continuous refill behavior
- [x] Confirm design decisions support assignment interface contract

Related files:
- [PRD.md](C:/Users/Admin/Submissions/submission/System_Design_Files/PRD.md)
- [Design.md](C:/Users/Admin/Submissions/submission/System_Design_Files/Design.md)

---

## Phase 3: Core Implementation

- [x] Implement per-customer bucket state model
- [x] Initialize first request with full bucket
- [x] Implement elapsed-time refill logic
- [x] Apply capacity capping after refill
- [x] Implement allow/deny decision logic
- [x] Implement `retry_after_ms` with correct ms conversion and ceiling
- [x] Add defensive handling for non-monotonic timestamps
- [x] Add config validation for invalid constructor inputs

Related files:
- [main.py](C:/Users/Admin/Submissions/submission/src/main.py)
- [types.py](C:/Users/Admin/Submissions/submission/src/types.py)
- [utils.py](C:/Users/Admin/Submissions/submission/src/utils.py)

---

## Phase 4: Testing and Verification

- [x] Add edge-case unit tests
- [x] Add assignment scenario test coverage
- [x] Validate per-customer isolation behavior
- [x] Validate retry timing and capacity behavior
- [x] Install and execute pytest in environment
- [x] Confirm full suite pass (`9 passed`)
- [x] Add pytest discovery guard for evaluator reliability

Related files:
- [test_edge_cases.py](C:/Users/Admin/Submissions/submission/tests/test_edge_cases.py)
- [test_scenario.py](C:/Users/Admin/Submissions/submission/tests/test_scenario.py)
- [pytest.ini](C:/Users/Admin/Submissions/submission/pytest.ini)

---

## Phase 5: Documentation and Submission Alignment

- [x] Align approach document with final implementation behavior
- [x] Update implementation notes to current architecture
- [x] Update AI usage log to strict evaluator template
- [x] Include PRD/design-first and compact-context rationale in AI log
- [x] Ensure all non-code docs are consistent with code and tests

Related files:
- [APPROACH.md](C:/Users/Admin/Submissions/submission/APPROACH.md)
- [IMPLEMENTATION_NOTES.md](C:/Users/Admin/Submissions/submission/IMPLEMENTATION_NOTES.md)
- [AI_USAGE_LOG.md](C:/Users/Admin/Submissions/submission/AI_USAGE_LOG.md)

---

## Final Readiness Checklist

- [x] Required folders and files present
- [x] Implementation aligned with assignment requirements
- [x] Tests passing
- [x] Documentation aligned
- [x] Submission ready
