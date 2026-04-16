## System Design: Token Bucket Rate Limiter

**Version**: 1.1  
**Date**: April 16, 2026  
**Architecture**: single-process, in-memory

---

## 1. Runtime Flow

For each request:
1. Load `BucketState` for `customer_id` (create if missing with full capacity).
2. Compute `elapsed_ms = max(0, now_ms - last_refill_ms)`.
3. Refill tokens continuously from elapsed time.
4. Cap tokens at capacity.
5. If tokens available (`>= 1 - epsilon`), consume 1 and allow.
6. Else deny and compute `retry_after_ms` using ceiling milliseconds.

---

## 2. Core Structures

```python
@dataclass
class BucketState:
    tokens: float
    last_refill_ms: int

class TokenBucketRateLimiter:
    capacity: int
    refill_rate: float
    buckets: Dict[str, BucketState]
```

---

## 3. Correctness Rules

- New customer starts with full bucket.
- Refill is on-demand, not timer driven.
- Token count never exceeds capacity.
- One allowed request consumes one token.
- Denied request returns:
  - `allowed = False`
  - `remaining = 0`
  - `retry_after_ms = ceil(((1 - tokens) / refill_rate) * 1000)`

---

## 4. Complexity

- Time per `check`: `O(1)`
- Space: `O(N)` for `N` active customers

---

## 5. Test Mapping

- Assignment scenario: [test_scenario.py](C:/Users/Admin/Submissions/submission/tests/test_scenario.py)
- Edge cases: [test_edge_cases.py](C:/Users/Admin/Submissions/submission/tests/test_edge_cases.py)
- Status: **9 tests passing**

---

## 6. Production Path

To scale horizontally, keep algorithm unchanged and move state to Redis with atomic read-update-write semantics (Lua script or equivalent).
