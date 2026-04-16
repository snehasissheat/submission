# Implementation Notes

**Date**: April 16, 2026  
**Language**: Python 3.14  
**Framework**: stdlib + pytest

---

## Final Design Summary

- Algorithm: token bucket with **on-demand refill** inside `check()`
- Per-customer state: `BucketState(tokens: float, last_refill_ms: int)`
- Initialization: new customer starts at full `capacity`
- Refill: `tokens += (elapsed_ms / 1000.0) * refill_rate`
- Cap: `tokens = min(tokens, capacity)`
- Allow rule: allow if `tokens >= 1 - 1e-9`, then consume 1 token
- Deny rule: `retry_after_ms = ceil(((1 - tokens) / refill_rate) * 1000)`

---

## Why These Choices

1. On-demand refill avoids background timers and scales better.
2. Float token storage preserves fractional refill precision.
3. Capacity capping enforces burst limits after long idle windows.
4. `ceil` retry conversion avoids returning `0ms` when a positive wait is required.
5. `max(0, elapsed_ms)` prevents backward timestamps from creating invalid behavior.

---

## Files Implemented

- [main.py](C:/Users/Admin/Submissions/submission/src/main.py)
- [types.py](C:/Users/Admin/Submissions/submission/src/types.py)
- [utils.py](C:/Users/Admin/Submissions/submission/src/utils.py)
- [test_edge_cases.py](C:/Users/Admin/Submissions/submission/tests/test_edge_cases.py)
- [test_scenario.py](C:/Users/Admin/Submissions/submission/tests/test_scenario.py)
- [simulate.py](C:/Users/Admin/Submissions/submission/demo/simulate.py)
- [pytest.ini](C:/Users/Admin/Submissions/submission/pytest.ini)

---

## Verification Status

- Command used: `python -m pytest -q`
- Result: **9 passed**
- Note: pytest cache warning may appear in this environment, but tests pass.

---

## Current Limitations

- In-memory/process-local state only
- No persistence across process restart
- No distributed synchronization
- No explicit locking for multi-threaded shared instance use
