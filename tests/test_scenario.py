from src.main import TokenBucketRateLimiter


def test_given_scenario():
    """
    Test the exact scenario from the assignment:
    T=0ms: 60 requests -> 40 tokens remaining
    T=2000ms: Refill 20 tokens -> 60 total
    T=2000ms: 70 requests -> 60 allowed, 10 denied
    """
    limiter = TokenBucketRateLimiter(100, 10)
    cid = "stripe-test"

    for _ in range(60):
        res = limiter.check(cid, 0)
        assert res.allowed

    assert limiter.buckets[cid].tokens == 40.0

    allowed = 0
    denied = 0
    for _ in range(70):
        res = limiter.check(cid, 2000)
        if res.allowed:
            allowed += 1
        else:
            denied += 1

    assert allowed == 60
    assert denied == 10


def test_assignment_recovery_and_cap_sequence():
    limiter = TokenBucketRateLimiter(100, 10)
    cid = "stripe-test"

    for _ in range(60):
        assert limiter.check(cid, 0).allowed

    for _ in range(70):
        limiter.check(cid, 2000)

    for _ in range(30):
        assert limiter.check(cid, 7000).allowed

    assert limiter.buckets[cid].tokens == 20.0

    first_after_cap = limiter.check(cid, 17000)
    assert first_after_cap.allowed
    assert first_after_cap.remaining == 99
