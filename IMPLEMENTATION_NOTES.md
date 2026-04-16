# Implementation Notes

**Date**: April 16, 2026  
**Language**: Python 3.14  
**Framework**: None (stdlib only)

---

## Design Decisions

### 1. On-Demand Refill (vs. Background Timer)
**Decision**: Calculate refill based on elapsed time when each request arrives, rather than using a background timer.

**Rationale**:
- Eliminates thread/resource overhead at scale
- Eliminates timing inaccuracies from discrete intervals
- O(1) per request; background timer would be O(N) per interval
- Matches industry standard (AWS, Stripe, CloudFlare)
- Production systems can port to Redis without rewriting logic

**Implementation**:
```python
elapsed_ms = current_time_ms - last_refill[customer_id]
tokens_to_add = (elapsed_ms / 1000.0) * refill_rate
```

### 2. Floating-Point Token Storage
**Decision**: Store token counts as `float`, not `int`.

**Rationale**:
- Continuous refill produces fractional tokens (e.g., 2.5 after 250ms at 10 tokens/sec)
- Ensures precision in retry calculations
- Final output still rounds to `int` for the API contract
- Without this, retry times would be innaccurate at millisecond level

**Trade-off**: Slightly higher memory per customer (float vs int); negligible at scale.

### 3. Capacity Capping After Every Refill
**Decision**: Apply `min(tokens, capacity)` after every refill, not just on initialization.

**Rationale**:
- Customers should not accumulate unbounded tokens during idle periods
- Long idle time could produce tokens >> capacity
- Ensures fairness: 1000-second idle doesn't give 10,000 seconds of unlimited requests
- Required by problem spec ("cap tokens at capacity")

**Implementation**:
```python
self.buckets[customer_id] = min_cap(self.buckets[customer_id], self.capacity)
```

### 4. Initialize New Customers at Full Capacity
**Decision**: New bucket starts with `capacity` tokens, not 0.

**Rationale**:
- Fixes the production incident: first request was incorrectly denied
- Matches expected behavior: fresh customer should be able to burst up to capacity
- Aligns with Token Bucket definition in literature
- Confirmed by problem statement example

### 5. Retry Calculation Formula
**Decision**: `retry_ms = int((1.0 - current_tokens) / refill_rate * 1000)`

**Rationale**:
- `1.0 - current_tokens` = tokens needed to reach 1 (threshold for allowing request)
- Divide by `refill_rate` = seconds until that many tokens are available
- Multiply by 1000 = convert to milliseconds
- Cast to `int` = match Decision contract

**Example**: If current_tokens = 0.7, refill_rate = 10:
- Need 0.3 more tokens
- Time = 0.3 / 10 = 0.03 seconds = 30 milliseconds

---

## Test Coverage

### Edge Cases Tested

1. **Initial Full Bucket**: First request on new customer succeeds with 99 remaining
2. **Retry Time Accuracy**: With 1 token/sec rate, waiting for 1 token returns exactly 1000ms
3. **Capacity Capping**: Long idle (100 seconds) doesn't exceed capacity
4. **Continuous Refill**: Accurate at arbitrary time boundaries (T=2000ms, T=7000ms)
5. **Burst Handling**: Multiple requests at same timestamp refill only once

### Test Files
- `test_edge_cases.py`: 3 focused unit tests
- `test_scenario.py`: 1 integration test matching problem specification
- `demo/simulate.py`: Demonstration of full scenario walkthrough

---

## Potential Improvements (Future)

### For Single-Instance (Current)
- [ ] Add logging for debugging rate limit events
- [ ] Add metrics collection (rejections per customer, retry frequency)
- [ ] Add TTL-based cleanup of inactive customer buckets
- [ ] Add customer configuration API (dynamic rate adjustments)

### For Production
- [ ] Port to Redis for distributed systems
  - Use Lua atomic script for refill + decision logic
  - Enables horizontal scaling across instances
- [ ] Add concurrency handling (locks or atomic Redis operations)
- [ ] Implement tiered rate limits (free vs premium customers)
- [ ] Add time-window decay for customer tiers
- [ ] Integrate with monitoring/alerting (Datadog, Prometheus)

### Performance Tuning
- Cache capacity values to reduce dictionary lookups
- Use array-based storage instead of dict for high-frequency customers
- Consider batch initialization for predictable customer sets

---

## Known Limitations

1. **No Concurrency**: Single-threaded only; needs locking for multi-threaded use
2. **Memory Persistence**: In-memory only; no recovery after restart
3. **Manual Cleanup**: Inactive customer buckets must be periodically removed
4. **No Distribution**: Only works within single Python process
5. **Float Precision**: Millisecond precision bounded by float64 representation (~15 significant digits)

---

## Verification

All tests pass:
- ✓ `test_initial_full_bucket`: Bucket initialization correct
- ✓ `test_retry_time`: Retry calculation accurate to millisecond
- ✓ `test_cap`: Capacity capping prevents overflow
- ✓ `test_given_scenario`: Full scenario walkthrough matches specification

Integration with demo validates end-to-end behavior.