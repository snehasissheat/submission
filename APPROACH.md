## Candidate Name: Snehasis SHit
## Language: Python
## Date: April 16, 2026

---

## 1. Problem Understanding

### Objective
Implement a token bucket rate limiter for a multi-tenant SaaS API that:
- Allows fair API usage across thousands of customers
- Enables short bursts while enforcing long-term rate limits
- Returns accurate retry guidance when requests are denied

### Core Mechanism
Each customer maintains an independent bucket with:
- **Capacity**: Maximum tokens the bucket can hold (e.g., 100)
- **Refill Rate**: Tokens added per second (e.g., 10 tokens/sec)
- **Token Consumption**: 1 token per request

Request Handling Logic:
- **Allow**: If tokens ≥ 1, consume 1 token and permit request
- **Deny**: If tokens < 1, return retry time in milliseconds

### Key Challenges
1. **Continuous Refill**: Tokens accumulate based on elapsed time, not discrete intervals
2. **Precision**: Fractional tokens occur; must handle both internally and in output
3. **Edge Cases**: First request, timing boundaries, capacity capping
4. **Accuracy**: Retry guidance must be precise to millisecond for client coordination

---

## 2. Assumptions

1. **External Time Source**: `current_time_ms` provided as input parameter (monotonically increasing)
2. **Token Consumption**: Exactly 1 token per request (fixed, non-configurable)
3. **Continuous Refill**: Refill = elapsed_ms / 1000 × refill_rate (not discrete intervals)
4. **Internal Precision**: Tokens stored as floats for fractional accuracy
5. **Output Format**: Remaining tokens exposed as integer (floor of current value)
6. **Per-Customer Isolation**: No shared state between customers; each bucket is independent
7. **Single-Threaded**: No concurrent request handling within a single limiter instance
8. **Time Monotonicity**: Current time never decreases (monotonically increasing)
9. **Return Unit**: `retry_after_ms` in milliseconds (despite suffix ambiguity in earlier docs)

---

## 3. Deliberate Errors Found in Problem Statement

1. **Background Timer Suggestion (Section 3, Suggested Approach)**
   - **Error**: "Implement a background timer that fires every 1 second and adds refill_rate tokens"
   - **Why Misleading**: Background timers are problematic:
     - Don't scale to thousands of customers (thread/resource overhead)
     - Introduce jitter and inaccuracy
     - Require explicit synchronization mechanisms
   - **Correct Interpretation**: Refill on-demand using elapsed time (lazy evaluation)
   - **Production Reality**: Cloud systems use on-demand calculation for rate limiting (AWS, Stripe, etc.)

2. **Ambiguous retry_after_ms Units**
   - **Error**: Field documentation unclear—earlier context suggests seconds
   - **Why Incorrect**: Field name explicitly says "ms" (milliseconds)
   - **Correct Behavior**: Return milliseconds; conversion needed from seconds
   - **Example**: If 1 second needed, return 1000, not 1

3. **Incomplete Refill Timing Explanation**
   - **Error**: Example states "Refill: 40 + (2 × 10)" without clear unit conversion
   - **Why Confusing**: Doesn't explicitly show elapsed time / 1000 calculation
   - **Correct Formula**: tokens_added = (elapsed_ms / 1000) × refill_rate

4. **Missing Rounding Boundaries**
   - **Error**: Example shows exact capacity capping but doesn't address fractional precision
   - **Issue**: Precision affects corner cases (e.g., retry calculations, remaining token display)
   - **Correct Approach**: Store floats internally, floor when returning remaining count

---

## 4. Bugs Found in Starter Code

### Bug #1: Initial Bucket at Zero (Line 21)
```python
self.buckets[customer_id] = 0  # BUGGY
```
- **Issue**: First request immediately denied despite having capacity
- **Root Cause**: Production incident mention confirms this breaks customer experience
- **Fix**: Initialize at full capacity
```python
self.buckets[customer_id] = float(self.capacity)
```

### Bug #2: Missing Capacity Cap After Refill
```python
self.buckets[customer_id] += tokens_to_add
# No cap applied!
```
- **Issue**: Tokens can exceed capacity (e.g., after long idle periods)
- **Root Cause**: Continuous refill without overflow check
- **Fix**: Apply min() after refill
```python
self.buckets[customer_id] = min(self.buckets[customer_id], self.capacity)
```

### Bug #3: retry_after_ms in Wrong Unit (Line XX)
```python
retry_after_ms = int(retry_after_seconds)  # Returns seconds, not ms!
```
- **Issue**: Client receives 1 when should receive 1000, causing 1000x faster retries
- **Root Cause**: Unit conversion omitted
- **Fix**: Multiply by 1000
```python
retry_after_ms = int(retry_after_seconds * 1000)
```

### Bug #4: Integer-Only Token Storage
```python
self.buckets[customer_id] = int(capacity)
```
- **Issue**: Integer arithmetic loses precision; fractional refills become 0
- **Root Cause**: Continuous refill formula requires fractional token tracking
- **Fix**: Use float type for storage
```python
self.buckets[customer_id] = float(capacity)  # Preserves 0.5, 0.25, etc.
```

### Bug #5: Hidden KeyError in _refill() - PRODUCTION CRASH RISK
```python
def _refill(self, customer_id: str, current_time_ms: int):
    last_time = self.last_refill[customer_id]  # KeyError if not initialized!
    elapsed_ms = max(0, current_time_ms - last_time)
```
- **Issue**: Direct dictionary access crashes if customer not yet initialized
- **Root Cause**: current code assumes initialization always happens in check(), but _refill() is public method
- **Risk**: If someone calls _refill() before check(), or if refactoring later, crash happens
- **Fix**: Use .get() method to handle missing keys
```python
last_time = self.last_refill.get(customer_id, current_time_ms)  # Default to current time if missing
```

### Bug #6: Precision Loss in retry_after_ms Rounding
```python
retry_after_ms = int(retry_after_seconds * 1000)  # Floors value!
```
- **Example**: retry_after_seconds = 0.0004 → int(0.4) = 0 ms (WRONG!)
- **Issue**: Client told to retry immediately (0 ms) when should wait 1+ ms
- **Root Cause**: int() truncates/floors instead of rounding up
- **Fix**: Use math.ceil() to round UP
```python
import math
retry_after_ms = math.ceil(retry_after_seconds * 1000)  # 0.0004s → 1ms (CORRECT)
```
- **Why It Matters**: In low-traffic scenarios with slow refill rates, retry times < 1ms are common
- **Consistency**: retry_after_ms field name promises milliseconds; must deliver milliseconds

### Bug #7: Floating-Point Comparison Precision
```python
if current_tokens >= 1:  # May fail due to floating-point rounding errors
```
- **Issue**: After many operations, current_tokens might be 0.9999999 or 1.0000001 due to precision drift
- **Example**: 100 - 99 × 1.0 might accumulate to 0.9999999 instead of 1.0
- **Fix**: Use epsilon comparison
```python
if current_tokens >= 1 - 1e-9:  # Allows tiny precision drift
```
- **Why It Matters**: Long-lived connections with many requests will accumulate floating-point errors

---

## 5. Solution Design

### Algorithm: On-Demand Refill (O(1) per request)

```
function check(customer_id, current_time_ms):
    // Step 1: Initialize on first request
    if customer_id not in buckets:
        buckets[customer_id] = capacity
        last_refill[customer_id] = current_time_ms
    
    // Step 2: Refill based on elapsed time
    elapsed_ms = current_time_ms - last_refill[customer_id]
    tokens_to_add = (elapsed_ms / 1000.0) * refill_rate
    buckets[customer_id] += tokens_to_add
    buckets[customer_id] = min(buckets[customer_id], capacity)  // Cap
    last_refill[customer_id] = current_time_ms
    
    // Step 3: Make decision
    current_tokens = buckets[customer_id]
    
    if current_tokens >= 1:
        buckets[customer_id] -= 1
        return Decision(allowed=true, remaining=int(buckets[customer_id]), retry_after_ms=0)
    else:
        tokens_needed = 1.0 - current_tokens
        retry_seconds = tokens_needed / refill_rate
        retry_ms = int(retry_seconds * 1000)
        return Decision(allowed=false, remaining=0, retry_after_ms=retry_ms)
```

### Data Structures

```
TokenBucketRateLimiter:
  - capacity: int                           // Max tokens per bucket
  - refill_rate: float                      // Tokens per second
  - buckets: Dict[str, float]               // Customer ID → Token count (fractional)
  - last_refill: Dict[str, int]             // Customer ID → Last refill timestamp (ms)
```

**Why float for buckets:**
- Continuous refill produces fractional tokens (e.g., 2.5 after 250ms at 10 tokens/sec)
- Ensures accuracy in retry calculations
- No precision loss when computing elapsed time

### Why This Approach

| Aspect | Benefit |
|--------|---------|
| **On-Demand Refill** | No background threads; scales to any number of customers |
| **O(1) Complexity** | Dictionary lookup and arithmetic; no loops or dependencies |
| **Accuracy** | Millisecond-precise based on actual elapsed time |
| **Distributed Ready** | Can move storage to Redis; logic stays identical |
| **Memory Efficient** | Only N entries for N active customers; old buckets cleaned as needed |

---

## 6. Complete Example Scenario Walkthrough

### Configuration
- capacity = 100 tokens
- refill_rate = 10 tokens/second

### T = 0 ms: Initial Request
```
Action: 1st request arrives
Bucket: NEW → Initialize with 100 tokens
Last refill: 0 ms
Decision: ALLOW (consume 1)
Remaining: 99
```

### T = 0 ms: Burst of 60 Requests
```
Elapsed: 0 ms (same timestamp batch)
Refill: 0 tokens
Before each request: ~99, 98, 97, ... 40
Decision: All 60 ALLOW
Remaining: 40
Bucket state: 40 tokens, last_refill = 0 ms
```

### T = 2000 ms: Refill Occurs
```
Elapsed: 2000 - 0 = 2000 ms = 2 sec
Refilled: 40 + (2 × 10) = 60 tokens
Cap applied: min(60, 100) = 60
Last refill: 2000 ms
```

First request at T=2000ms:
```
Decision: ALLOW (consume 1)
Remaining: 59
```

Next 70 requests at T=2000ms:
```
Elapsed: 0 ms (same timestamp)
Refill: 0 (no additional time)
Tokens available: 59, 58, 57, ..., 0
Decision: 59 ALLOW, 1 DENY
Retry for denied: (1.0 - 0) / 10 = 0.1 sec = 100 ms
```

### T = 7000 ms: Second Refill
```
Elapsed: 7000 - 2000 = 5000 ms = 5 sec
Refilled: 0 + (5 × 10) = 50 tokens (50 < 100, no cap needed)
Last refill: 7000 ms

30 requests arrive:
Decision: All 30 ALLOW
Remaining: 20
```

### T = 17000 ms: Long Idle, Capacity Cap
```
Elapsed: 17000 - 7000 = 10000 ms = 10 sec
Calculated: 20 + (10 × 10) = 120 tokens
Cap applied: min(120, 100) = 100 ← Capped at capacity
Last refill: 17000 ms

80 requests arrive:
Decision: All 80 ALLOW
Remaining: 20
Bucket state: 20 tokens, last_refill = 17000 ms
```

### Edge Cases Tested

1. **First Request**: Initialized at capacity ✓
2. **Fractional Refill**: 250 ms at 10 tokens/sec = 2.5 tokens ✓
3. **Capacity Capping**: Long idle periods don't overflow ✓
4. **Retry Calculation**: (1 - 0.3) / 10 = 70 ms (rounded correctly) ✓
5. **Same Timestamp**: Multiple requests at same ms don't double-refill ✓

---

## 7. Complexity Analysis

| Metric | Complexity | Notes |
|--------|-----------|-------|
| **Time per request** | O(1) | Dictionary lookup, arithmetic, no loops |
| **Space per customer** | O(1) | Two floats per customer (tokens, timestamp) |
| **Total space for N customers** | O(N) | Linear in active customer count |
| **Memory cleanup** | Manual or TTL-based | In production, remove stale entries periodically |

---

## 8. Production Considerations

### Thread Safety (⚠️ NOT IMPLEMENTED - BY DESIGN)
- **Current Implementation**: Single-threaded, no locks
- **Data Structures at Risk**: 
  - `self.buckets` (Dict[str, float])
  - `self.last_refill` (Dict[str, int])
- **Vulnerability**: Race condition if concurrent requests for same customer
  - Thread A reads tokens = 1.0, decides ALLOW
  - Thread B reads tokens = 1.0, decides ALLOW (both consumed same token!)
- **Production Fix**: 
  - Use `threading.Lock` per customer
  - OR move to Redis with Lua atomicity
  - OR use thread-safe concurrent.futures.ThreadPoolExecutor with per-customer queuing

### Current Deployment Constraints
- ✅ Safe for: Single-threaded async (Node.js event loop style)
- ✅ Safe for: ASGI/WSGI with process-per-request (no shared state)
- ❌ NOT Safe for: Multi-threaded Flask/FastAPI without locks
- ❌ NOT Safe for: Gunicorn with threading workers

### Scalability
- **Current**: In-memory dictionaries (single-instance)
- **Production**: Replace with Redis (multi-instance, distributed)
- **Lua Script**: Atomic refill + decision logic using Redis scripts

### Concurrency
- **Current**: Single-threaded (no locking needed)
- **Production**: Add locks per customer or use atomic Redis operations

### Monitoring
- Track: rejection rate, retry patterns, burst frequency
- Alert: if any customer consistently hitting limits

### Future Enhancements
- Per-endpoint rate limits (different tiers)
- Adaptive limits based on customer tier
- Distributed rate limiting across multiple data centers