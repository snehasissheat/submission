## Product Requirement Document (PRD)

**Version**: 1.0  
**Date**: April 16, 2026  
**Status**: Approved for Production  
**Assignment**: Token Bucket Rate Limiter (Campus Screening 2026)

---

## 1. Executive Summary

Implement a multi-tenant token bucket rate limiter for a SaaS API that ensures fair usage across customers, prevents abuse, and allows controlled bursts while enforcing long-term rate limits. The system must provide accurate retry guidance to clients when requests are denied.

---

## 2. Problem Statement

**Current Situation**:
- Production incidents: Customers rate-limited on first request
- Retry guidance was inaccurate or missing (retry_after_ms = 0)
- Inconsistent behavior across customer buckets

**Business Impact**:
- Customer frustration and support tickets
- Perceived service unreliability
- Potential loss of customer trust

**Solution Scope**: Implement Token Bucket algorithm with on-demand refill for accuracy and scalability.

---

## 3. Functional Requirements

### 3.1 Core Rate Limiting

| Requirement | Details |
|-------------|---------|
| **Per-Customer Isolation** | Each customer has independent token bucket |
| **Token Consumption** | 1 token per request (fixed, non-negotiable) |
| **Capacity Enforcement** | Bucket holds max `capacity` tokens |
| **Continuous Refill** | Tokens added based on elapsed time at `refill_rate` tokens/sec |
| **Request Allowance** | Allow request if tokens ≥ 1; consume 1 token |
| **Request Denial** | Deny request if tokens < 1; return retry time |
| **Initial State** | New customer bucket initialized at full capacity |
| **Burst Support** | Up to `capacity` consecutive requests allowed |

### 3.2 Retry Guidance

| Requirement | Details |
|-------------|---------|
| **Return Format** | `Decision` object with: `allowed`, `remaining`, `retry_after_ms` |
| **Unit Accuracy** | Return time in milliseconds (despite ambiguous naming) |
| **Precision** | Must be accurate to nearest millisecond |
| **Failed Request** | `remaining = 0`, `retry_after_ms = (tokens_needed / refill_rate) × 1000` |
| **Allowed Request** | `remaining = int(current_tokens - 1)`, `retry_after_ms = 0` |

### 3.3 Example Configuration

```
Customer: stripe-test
Capacity: 100 tokens
Refill Rate: 10 tokens/second
```

**Scenario**:
- T=0ms: Initialize with 100 tokens
- T=0ms: 60 requests → 60 consumed → 40 remaining
- T=2000ms: Refill = 2 sec × 10 = 20 tokens added → 60 total
- T=2000ms: 70 requests → 60 allowed, 10 denied
- T=7000ms: Refill = 5 sec × 10 = 50 tokens → 50 total
- T=7000ms: 30 requests → all allowed, 20 remaining

---

## 4. Non-Functional Requirements

| Aspect | Requirement | Target |
|--------|-------------|--------|
| **Performance** | Latency per check() call | < 1ms (O(1) complexity) |
| **Throughput** | Requests per second | No limit; O(1) per request |
| **Memory** | Per active customer | ~50 bytes (2 floats + ID overhead) |
| **Scalability** | Active customers supported | 100,000+ in-memory; unlimited with Redis |
| **Accuracy** | Time-based refill precision | ±1 millisecond |
| **Availability** | Uptime requirement | 99.9% (single instance) |
| **Concurrency** | Thread safety | Single-threaded (current); add locks for multi-threaded |

---

## 5. Success Criteria

### 5.1 Functional Success
- ✓ No customer exceeds configured rate limit (long-term average)
- ✓ No valid request denied incorrectly (e.g., first request allowed)
- ✓ Retry time accurate to millisecond precision
- ✓ Tokens never exceed capacity (even after long idle)
- ✓ Fractional refills handled correctly

### 5.2 Quality Metrics
- ✓ All edge cases tested (first request, burst, idle, capping)
- ✓ Code reviewed against APPROACH.md
- ✓ AI usage logged and justified
- ✓ No production incidents in testing

### 5.3 Deployment Readiness
- ✓ Implementation complete and tested
- ✓ Documentation complete (APPROACH.md, design, implementation notes)
- ✓ Demo runnable end-to-end
- ✓ Code review checklist passed

---

## 6. Technical Specifications

### 6.1 Interface Contract

```python
class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize rate limiter.
        
        Args:
            capacity: Max tokens per bucket (e.g., 100)
            refill_rate: Tokens added per second (e.g., 10.0)
        """
    
    def check(self, customer_id: str, current_time_ms: int) -> Decision:
        """
        Check if request is allowed and return decision.
        
        Args:
            customer_id: Unique customer identifier
            current_time_ms: Current time in milliseconds (monotonically increasing)
        
        Returns:
            Decision(allowed: bool, remaining: int, retry_after_ms: int)
        """
```

### 6.2 Data Model

```python
@dataclass
class Decision:
    allowed: bool          # True if request permitted
    remaining: int         # Tokens left after decision (0 if denied)
    retry_after_ms: int    # Milliseconds to wait before retry (0 if allowed)
```

### 6.3 Algorithm

**Input**: customer_id, current_time_ms  
**Output**: Decision

```
1. If customer new:
     Initialize: tokens = capacity, last_refill = current_time_ms
2. Compute elapsed time:
     elapsed_ms = current_time_ms - last_refill
3. Refill based on elapsed time:
     tokens_to_add = (elapsed_ms / 1000.0) × refill_rate
     tokens = min(tokens + tokens_to_add, capacity)
4. Update timestamp:
     last_refill = current_time_ms
5. Make decision:
     If tokens ≥ 1:
       tokens -= 1
       Return Decision(allowed=true, remaining=int(tokens), retry_after_ms=0)
     Else:
       tokens_needed = 1.0 - tokens
       retry_ms = int((tokens_needed / refill_rate) × 1000)
       Return Decision(allowed=false, remaining=0, retry_after_ms=retry_ms)
```

---

## 7. Implementation Approach

### 7.1 Design Choice: On-Demand Refill

**Selected Approach**: Calculate refill based on elapsed time when each request arrives.

**Rationale**:
- No background threads → scales to millions of customers
- O(1) per request (dictionary lookup + arithmetic)
- Millisecond accuracy (no timing jitter from discrete intervals)
- Industry standard (AWS Lambda, Stripe, CloudFlare)
- Easily distributable (move to Redis without algorithm change)

**Alternative Rejected**: Background timer (every 1 second add tokens)
- Cons: O(N) per interval; thread overhead; timing inaccuracy; scale limits

### 7.2 Storage Layer

**Current Implementation**: In-memory Python dictionaries
- `buckets: Dict[str, float]` — token count per customer
- `last_refill: Dict[str, int]` — timestamp per customer

**Production Path**: Redis for distributed systems
- Replaces dict with Redis strings
- Uses Lua atomic script for refill + decision in single operation
- Enables horizontal scaling across servers

---

## 8. Future Enhancements

### 8.1 Phase 2: Advanced Features
- Per-endpoint rate limits (different limits for different API methods)
- Tier-based limits (free vs premium vs enterprise customers)
- Burst allowance configuration (separate burst_capacity from sustained_rate)

### 8.2 Phase 3: Distribution
- Redis backend for multi-instance deployment
- Distributed locking for concurrent customer requests
- Cross-datacenter synchronization

### 8.3 Phase 4: Observability
- Metrics: rejections/customer, retry frequency, burst patterns
- Alerts: customer hitting limits repeatedly, anomalous patterns
- Dashboard: per-customer quota usage in real-time

### 8.4 Phase 5: Intelligence
- Dynamic rate adjustment based on usage patterns
- Customer-specific burst windows
- Predictive queueing for high-traffic periods

---

## 9. Testing & Acceptance

### 9.1 Test Coverage
- ✓ Initial bucket at full capacity (not 0)
- ✓ Retry time accuracy (millisecond precision)
- ✓ Capacity capping (prevents overflow)
- ✓ Full scenario walkthrough (matching problem specification)

### 9.2 Acceptance Criteria
- ✓ All tests pass
- ✓ Zero known bugs
- ✓ Code matches APPROACH.md design
- ✓ AI usage logged and reviewed
- ✓ Production deployment checklist cleared

---

## 10. Success Checklist

| Item | Status |
|------|--------|
| Core logic implemented | ✓ Complete |
| All bugs identified and fixed | ✓ Complete |
| Tests passing | ✓ 4/4 pass |
| APPROACH.md complete | ✓ Complete (8 sections) |
| AI_USAGE_LOG.md complete | ✓ Complete |
| Design documentation | ✓ Complete |
| Ready for production | ✓ Yes |