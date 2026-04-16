## Product Requirements Document (PRD)

**Version**: 1.1  
**Date**: April 16, 2026  
**Assignment**: Token Bucket Rate Limiter

---

## 1. Objective

Build a per-customer token bucket limiter that:
- allows short bursts up to capacity
- enforces long-run rate via continuous refill
- returns accurate retry guidance in milliseconds

---

## 2. Functional Requirements

1. Per-customer isolated bucket state.
2. New bucket starts full (`capacity` tokens).
3. Each allowed request consumes exactly 1 token.
4. Refill is continuous from elapsed time (not interval timer based).
5. Tokens are capped at `capacity`.
6. Denied requests return `remaining = 0` and correct `retry_after_ms`.
7. Interface:
   - `check(customer_id: str, current_time_ms: int) -> Decision`
   - `Decision { allowed: bool, remaining: int, retry_after_ms: int }`

---

## 3. Algorithm Contract

- Refill math: `(elapsed_ms / 1000.0) * refill_rate`
- Deny retry math: `ceil(((1 - current_tokens) / refill_rate) * 1000)`
- Millisecond output required for `retry_after_ms`

---

## 4. Data Model

```python
@dataclass
class Decision:
    allowed: bool
    remaining: int
    retry_after_ms: int

@dataclass
class BucketState:
    tokens: float
    last_refill_ms: int
```

Store:
- `buckets: Dict[str, BucketState]`

---

## 5. Example Acceptance Scenario

Configuration:
- `capacity = 100`
- `refill_rate = 10 tokens/sec`
- customer: `stripe-test`

Expected:
- `T=0`: first request allowed; bucket starts full
- `T=0`, 60 requests: 40 tokens remain
- `T=2000`, 70 requests: 60 allowed, 10 denied
- `T=7000`, 30 requests: all allowed, 20 remain
- `T=17000`, 80 requests: all allowed after cap, 20 remain

---

## 6. Non-Functional Requirements

- `O(1)` time per request
- `O(N)` memory for N active customers
- deterministic behavior with same inputs
- defensive handling for non-monotonic timestamps

---

## 7. Verification

- Automated tests executed with `python -m pytest -q`
- Current status: **9 passed**
