## Candidate Name: Snehasis SHit
## Language: Python
## Date: April 16, 2026

---

## 1. Problem Understanding

### Objective
Implement a token bucket rate limiter for a multi-tenant SaaS API that:
- Allows fair API usage across thousands of customers
- Supports short bursts up to bucket capacity
- Enforces the long-run average rate using continuous refill
- Returns correct retry guidance when a request is denied

### Core Mechanism
Each customer has an independent bucket with:
- **Capacity**: maximum number of tokens it can hold
- **Refill Rate**: tokens added per second
- **Consumption Rule**: each allowed request consumes 1 token

### Required Request Behavior
- **Allow** when the bucket has at least 1 token, then consume 1 token
- **Deny** when the bucket has less than 1 token
- **Refill continuously** based on elapsed time since the last processed request
- **Cap** token count at capacity
- **Return** `allowed`, `remaining`, and `retry_after_ms`

---

## 2. Assumptions

1. `current_time_ms` is provided by the caller for every request.
2. Each request consumes exactly 1 token.
3. Tokens are stored internally as floating-point values to preserve fractional refill precision.
4. `remaining` in the response is the integer floor of the post-decision token count.
5. Buckets are maintained independently for each customer.
6. This implementation is single-process and in-memory.
7. The implementation should be robust even if timestamps are non-monotonic; negative elapsed time should not create tokens.
8. `retry_after_ms` must be returned in milliseconds.

---

## 3. Deliberate Errors Found in Problem Statement

1. **Background timer suggestion is misleading**
   - The prompt suggests a 1-second background refill timer.
   - This conflicts with the actual requirement to refill continuously based on elapsed time since the last request.
   - The correct approach is lazy, on-demand refill during `check()`.

2. **`retry_after_ms` description is contradictory**
   - The prompt says the field should equal the number of seconds to wait, but the field name and interface say milliseconds.
   - The correct unit is milliseconds.

3. **Refill math is shown without explicit millisecond conversion**
   - The examples use `2 × 10` and `5 × 10`, but the interface time input is in milliseconds.
   - The actual formula is `(elapsed_ms / 1000.0) * refill_rate`.

4. **The prompt mixes exact examples with underspecified precision rules**
   - Continuous refill implies fractional tokens.
   - The implementation must store floats internally and only floor when returning `remaining`.

---

## 4. Bugs Found in Starter Code

### Bug #1: Bucket initialized empty instead of full
- **Issue**: First request can be denied incorrectly.
- **Fix**: Initialize new customers with `capacity` tokens.

### Bug #2: Missing capacity cap after refill
- **Issue**: Long idle periods can overflow the bucket.
- **Fix**: Clamp token count with `min(tokens, capacity)`.

### Bug #3: Wrong `retry_after_ms` unit
- **Issue**: Returning seconds instead of milliseconds gives bad client guidance.
- **Fix**: Convert seconds to milliseconds.

### Bug #4: Integer-only token accounting
- **Issue**: Fractional refill is lost.
- **Fix**: Store tokens as `float`.

### Bug #5: Retry time rounded down
- **Issue**: Truncation can produce `0 ms` when a small positive wait is required.
- **Fix**: Use `math.ceil()` when converting to milliseconds.

### Bug #6: Floating-point comparison edge cases
- **Issue**: A value like `0.999999999` can be denied incorrectly.
- **Fix**: Allow with a small epsilon margin.

### Bug #7: Unsafe handling of backward timestamps
- **Issue**: Negative elapsed time could corrupt refill logic.
- **Fix**: Clamp elapsed time to `>= 0`.

---

## 5. Solution Design

### Algorithm: On-Demand Token Bucket

For each `check(customer_id, current_time_ms)` call:

1. If the customer has no bucket yet, create one with:
   - `tokens = capacity`
   - `last_refill_ms = current_time_ms`

2. Refill using elapsed time:
   - `elapsed_ms = max(0, current_time_ms - last_refill_ms)`
   - `tokens += (elapsed_ms / 1000.0) * refill_rate`
   - `tokens = min(tokens, capacity)`
   - `last_refill_ms = max(last_refill_ms, current_time_ms)`

3. Make a decision:
   - If `tokens >= 1` (with epsilon tolerance), allow and subtract 1
   - Otherwise deny and compute:
     - `tokens_needed = 1 - tokens`
     - `retry_after_ms = ceil((tokens_needed / refill_rate) * 1000)`

### Data Structure

```
BucketState:
  - tokens: float
  - last_refill_ms: int

TokenBucketRateLimiter:
  - capacity: int
  - refill_rate: float
  - buckets: Dict[str, BucketState]
```

### Why this design
- `O(1)` time per request
- No background workers or timers
- Precise continuous refill behavior
- Easy to extend to Redis or another shared store later

---

## 6. Example Scenario Walkthrough

### Configuration
- capacity = 100
- refill_rate = 10 tokens/second
- customer = `stripe-test`

### T = 0 ms
- First request initializes the bucket at 100 tokens.
- After serving 60 requests at the same timestamp:
  - `100 - 60 = 40`
- Bucket now has **40 tokens**.

### T = 2000 ms
- Elapsed time = 2000 ms = 2 seconds
- Refill = `2 * 10 = 20`
- Bucket becomes `40 + 20 = 60`
- 70 requests arrive at `T=2000ms`:
  - 60 are allowed
  - 10 are denied
- Bucket ends at **0 tokens**.

### T = 7000 ms
- Elapsed time = 5000 ms = 5 seconds
- Refill = `5 * 10 = 50`
- Bucket becomes **50**
- 30 requests arrive:
  - all 30 are allowed
- Bucket ends at **20 tokens**

### T = 17000 ms
- Elapsed time = 10000 ms = 10 seconds
- Refill = `10 * 10 = 100`
- Bucket would become `20 + 100 = 120`, but must be capped at 100
- 80 requests arrive:
  - all 80 are allowed
- Bucket ends at **20 tokens**

### Edge Cases to Test
1. First request is allowed and starts from a full bucket.
2. Denied requests return a non-zero `retry_after_ms` when appropriate.
3. Fractional refill produces correct retry timing.
4. Buckets never exceed capacity after long idle periods.
5. Multiple customers do not affect each other.
6. Backward timestamps do not create tokens.

---

## 7. Complexity Analysis

| Metric | Complexity |
|--------|------------|
| Time per request | O(1) |
| Space per customer | O(1) |
| Total space for N customers | O(N) |

---

## 8. Production Considerations

- Current implementation is in-memory and process-local.
- For multi-instance deployment, shared state should move to a store like Redis.
- For concurrent access in a threaded environment, bucket updates must be atomic.
- Stale customer state can be cleaned up with TTL or periodic eviction.
- Monitoring should track deny rate, retry timing, and hot customers.
