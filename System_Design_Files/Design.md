## System Design: Token Bucket Rate Limiter

**Version**: 1.0  
**Date**: April 16, 2026  
**Architecture**: Single-instance in-memory (Redis path documented for scale)

---

## 1. Architecture Overview

### 1.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Incoming Request                                             │
│ check(customer_id="stripe-test", current_time_ms=2000)     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │ Fetch Customer Bucket   │
        │ (Initialize if new)     │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────────┐
        │ Compute Elapsed Time        │
        │ (since last refill)         │
        └────────────┬────────────────┘
                     │
        ┌────────────▼────────────────┐
        │ Add Tokens                  │
        │ (elapsed_ms / 1000 * rate)  │
        └────────────┬────────────────┘
                     │
        ┌────────────▼────────────────┐
        │ Apply Capacity Cap          │
        │ (min(tokens, capacity))     │
        └────────────┬────────────────┘
                     │
        ┌────────────▼────────────────┐
        │ Check Token Availability    │
        │ (>= 1 allowed, < 1 denied)  │
        └────────────┬────────────────┘
                     │
        ┌────────────▼──────────────────────┐
        │ Return Decision                    │
        │ Allow: (true, remaining, 0)        │
        │ Deny: (false, 0, retry_ms)         │
        └──────────────────┬─────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Response    │
                    └─────────────┘
```

### 1.2 Component Diagram

```
┌──────────────────────────────────────────┐
│     TokenBucketRateLimiter API           │
├──────────────────────────────────────────┤
│ ┌────────────────────────────────────┐   │
│ │  check(customer_id, current_time)  │   │
│ │  → Decision                         │   │
│ └────────────┬───────────────────────┘   │
│              │                            │
│ ┌────────────▼──────────────────────┐    │
│ │  _refill() [Private]              │    │
│ │  - Compute elapsed time           │    │
│ │  - Add tokens                     │    │
│ │  - Apply cap                      │    │
│ └────────────────────────────────────┘    │
├──────────────────────────────────────────┤
│  Data Store                              │
│  ┌──────────────┐  ┌──────────────────┐ │
│  │ buckets[]    │  │ last_refill[]    │ │
│  │Dict[str->f] │  │ Dict[str->int]   │ │
│  └──────────────┘  └──────────────────┘ │
└──────────────────────────────────────────┘
```

---

## 2. Core Components

### 2.1 Rate Limiter Core (`main.py`)

**Responsibilities**:
- Manage customer buckets
- Compute refill logic
- Make allow/deny decisions
- Return accurate retry times

**Key Methods**:
- `__init__(capacity, refill_rate)` — Initialize limiter
- `check(customer_id, current_time_ms)` — Check request; return Decision
- `_refill(customer_id, current_time_ms)` — [Internal] Refill tokens

**Complexity**:
- Time: O(1) per request
- Space: O(N) for N active customers

### 2.2 Type Definitions (`types.py`)

```python
@dataclass
class Decision:
    allowed: bool       # Request permitted?
    remaining: int      # Tokens left after decision
    retry_after_ms: int # Milliseconds until retry (0 if allowed)
```

### 2.3 Utilities (`utils.py`)

```python
def min_cap(value: float, capacity: int) -> float:
    """Cap token count at capacity."""
    return min(value, capacity)
```

### 2.4 Time Source

**Contract**: External timestamp passed as `current_time_ms` parameter
- Assumption: Monotonically increasing (never decreases)
- Origin: Caller-controlled (system time, mock time, etc.)
- Unit: Milliseconds

---

## 3. Data Model

### 3.1 Customer Bucket State

```python
buckets = {
    "stripe-test": 40.5,        # Current token count (float)
    "acme-corp": 99.0,
    "startup-xyz": 0.3,
}

last_refill = {
    "stripe-test": 2000,        # Last refill timestamp (ms)
    "acme-corp": 1950,
    "startup-xyz": 1999,
}
```

**Why float for tokens?**
- Continuous refill at arbitrary rates produces fractional tokens
- Example: 250 ms at 10 tokens/sec = 2.5 tokens
- Without floats, precision loss ruins retry calculations

### 3.2 Configuration Parameters

```python
limiter = TokenBucketRateLimiter(
    capacity=100,        # Max tokens per bucket
    refill_rate=10.0     # Tokens per second
)
```

---

## 4. Algorithm Detail

### 4.1 Refill Calculation

```
elapsed_ms = current_time_ms - last_refill[customer_id]
tokens_to_add = (elapsed_ms / 1000.0) * refill_rate
```

**Example**:
- Last refill: T=0 ms with 100 tokens
- Current time: T=2500 ms
- Elapsed: 2500 - 0 = 2500 ms = 2.5 seconds
- Tokens to add: 2.5 × 10 = 25 tokens
- New total: 100 + 25 = 125 → capped to 100

### 4.2 Retry Time Calculation

```
tokens_needed = 1.0 - current_tokens
retry_seconds = tokens_needed / refill_rate
retry_ms = int(retry_seconds * 1000)
```

**Example**:
- Current tokens: 0.3
- Refill rate: 10 tokens/sec
- Tokens needed: 1.0 - 0.3 = 0.7
- Time to acquire: 0.7 / 10 = 0.07 seconds
- In milliseconds: 0.07 × 1000 = 70 ms

### 4.3 Decision Logic

```
if current_tokens >= 1.0:
    ALLOW_REQUEST()
    tokens -= 1
    return Decision(allowed=True, remaining=int(tokens), retry_after_ms=0)
else:
    DENY_REQUEST()
    compute_retry_time()
    return Decision(allowed=False, remaining=0, retry_after_ms=retry_ms)
```

---

## 5. Storage Architecture

### 5.1 Single-Instance (Current)

```
Python Process
├── TokenBucketRateLimiter
│   ├── buckets: Dict (in-memory)
│   └── last_refill: Dict (in-memory)
└── [On restart: all state lost]
```

**Characteristics**:
- Fast: Direct memory access (< 1 µs)
- Limited: Single process only
- Ephemeral: No persistence

### 5.2 Distributed (Future: Redis)

```
┌─────────────────────────────────────┐
│ Multiple API Servers                │
│ (horizontal scaling)                │
└──────────────┬──────────────────────┘
               │
        ┌──────▼───────┐
        │ Redis Cluster │
        │ (persistent)  │
        │ (distributed) │
        └───────────────┘
```

**Migration Path**:
1. Replace in-memory dict with Redis client
2. Use Redis Lua script for atomic refill + decision
3. All algorithm logic unchanged

**Lua Script** (future):
```lua
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Get current bucket state
local bucket = redis.call('HGET', key, 'tokens') or capacity
local last_refill = redis.call('HGET', key, 'last_refill') or now

-- Refill with atomic operation
local elapsed = (now - last_refill) / 1000
local new_tokens = math.min(bucket + (elapsed * rate), capacity)

-- Store updated state
redis.call('HSET', key, 'tokens', new_tokens)
redis.call('HSET', key, 'last_refill', now)

-- Decision
if new_tokens >= 1 then
    return {1, new_tokens - 1}  -- [allowed, remaining]
else
    local retry = ((1 - new_tokens) / rate) * 1000
    return {0, retry}
end
```

---

## 6. Complexity Analysis

| Metric | Value | Notes |
|--------|-------|-------|
| **Time per check()** | O(1) | Dict lookup + arithmetic |
| **Space per customer** | O(1) | 2 floats (~16 bytes) |
| **Total space (N customers)** | O(N) | Linear growth with active customers |
| **Refill cost** | O(1) | No loops; direct calculation |
| **Decision cost** | O(1) | Single comparison + arithmetic |

**Scalability**:
- Single instance: 100,000+ customers feasible in-memory
- Distributed: Unlimited (with Redis sharding)

---

## 7. Edge Cases & Solutions

| Case | Scenario | Handling |
|------|----------|----------|
| **First Request** | New customer | Initialize at capacity (not 0) |
| **Same Timestamp** | Multiple requests at T=2000ms | Refill once; subsequent requests at same T don't refill again |
| **Long Idle** | Customer silent for 1000 seconds | Refill capped at capacity (not 10,000 tokens) |
| **Fractional Tokens** | 250ms at 10 tokens/sec | Store as 2.5; calculate retry with precision |
| **Microsecond Precision** | Current time T=2000.5ms | Handled by float arithmetic; no loss |
| **Rate Boundary** | Exactly 1 token available | Allow the request; on next denial, retry = 0 |

---

## 8. Scalability Path

### Stage 1: Single Instance (Current)
- ✓ Supports thousands of concurrent customers
- ✓ O(1) per request
- ✓ Suitable for startups, many SMBs
- Limitation: Single server; no high availability

### Stage 2: Redis Backend
- Deploy Redis cluster
- Replace dict with Redis hashes: `bucket:customer_id → {tokens, last_refill}`
- Use Lua script for atomicity
- Enables horizontal scaling

### Stage 3: Distributed Deployment
- Multiple API servers → Redis cluster
- Per-customer sharding (consistent hashing)
- Cross-datacenter replication for resilience
- Real-time metrics collection

### Stage 4: Advanced Features
- Per-endpoint tier configuration
- Adaptive burst allowance
- Machine learning for anomaly detection

---

## 9. Monitoring & Observability

### 9.1 Key Metrics

| Metric | Purpose |
|--------|---------|
| **Rejection Rate** | % of requests denied per customer |
| **Retry Latency** | Actual vs. calculated retry time |
| **Burst Pattern** | Spike detection per customer |
| **Bucket Capacity** | Avg tokens held per customer |

### 9.2 Alerts

- Customer hitting limits > 5 times/minute (potential abuse or genuine need)
- Retry accuracy deviation > 100ms (timing/precision issue)
- Storage growth anomaly (possible memory leak)

### 9.3 Logging

```python
# On allow
logger.debug(f"Allowed: {customer_id} @ {current_time_ms}ms, remaining={remaining}")

# On deny
logger.warning(f"Denied: {customer_id} @ {current_time_ms}ms, retry_ms={retry_after_ms}")
```

---

## 10. Testing Strategy

### 10.1 Unit Tests
- ✓ Initial bucket at capacity (not 0)
- ✓ Retry time millisecond accuracy
- ✓ Capacity capping after refill
- ✓ Fractional token handling

### 10.2 Integration Tests
- ✓ Full scenario: init → burst → refill → burst again
- ✓ Multi-customer isolation
- ✓ Long idle periods
- ✓ Timestamp boundary conditions

### 10.3 Stress Tests (Future)
- 100K concurrent customers
- Burst patterns at specific time intervals
- Redis backend failover

---

## 11. Deployment Checklist

- [x] Code implementation complete
- [x] All bugs fixed
- [x] Unit tests passing (4/4)
- [x] APPROACH.md complete & reviewed
- [x] AI usage logged
- [x] Design documentation complete
- [x] Demo runnable end-to-end
- [x] Ready for production

---

## 12. Production Deployment Notes

### 12.1 Fallback Behavior

If Redis becomes unavailable (future):
- Fall back to in-memory storage
- Lose historical state; buckets reset
- Temporary service degradation acceptable vs. outage

### 12.2 Capacity Planning

**Memory per customer**: ~16 bytes (2 floats)
- 1M customers: ~16 MB
- 10M customers: ~160 MB (needs Redis sharding)

**CPU per request**: < 1 µs (negligible)
- 1M req/sec: < 1 CPU core

### 12.3 SLA Requirements

- **Availability**: 99.9% uptime (single instance); 99.99% (with Redis HA)
- **Latency**: p95 < 1ms per request
- **Accuracy**: Retry time within ±1ms
- **Data Loss**: Acceptable (in-memory); prevent with Redis RDB/AOF