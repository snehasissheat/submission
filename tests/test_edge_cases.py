from src.main import TokenBucketRateLimiter


def test_initial_full_bucket():
    limiter = TokenBucketRateLimiter(100, 10)
    res = limiter.check("user1", 0)
    assert res.allowed
    assert res.remaining == 99


def test_retry_time():
    limiter = TokenBucketRateLimiter(1, 1)

    limiter.check("u", 0)
    res = limiter.check("u", 0)

    assert not res.allowed
    assert res.retry_after_ms == 1000


def test_cap():
    limiter = TokenBucketRateLimiter(100, 10)
    limiter.check("u", 0)

    res = limiter.check("u", 100000)
    assert res.remaining <= 99


def test_per_customer_state_is_isolated():
    limiter = TokenBucketRateLimiter(2, 1)

    first_a = limiter.check("customer-a", 0)
    first_b = limiter.check("customer-b", 0)
    second_a = limiter.check("customer-a", 0)
    denied_a = limiter.check("customer-a", 0)

    assert first_a.allowed
    assert first_b.allowed
    assert second_a.allowed
    assert not denied_a.allowed
    assert denied_a.retry_after_ms == 1000


def test_fractional_refill_allows_after_exact_wait():
    limiter = TokenBucketRateLimiter(1, 2)

    limiter.check("u", 0)
    denied = limiter.check("u", 250)
    allowed = limiter.check("u", 500)

    assert not denied.allowed
    assert denied.retry_after_ms == 250
    assert allowed.allowed
    assert allowed.remaining == 0


def test_non_monotonic_timestamp_does_not_create_tokens():
    limiter = TokenBucketRateLimiter(2, 1)

    limiter.check("u", 1000)
    limiter.check("u", 1000)
    denied = limiter.check("u", 500)

    assert not denied.allowed
    assert denied.retry_after_ms == 1000


def test_invalid_configuration_is_rejected():
    try:
        TokenBucketRateLimiter(0, 1)
        assert False, "expected ValueError for invalid capacity"
    except ValueError:
        pass

    try:
        TokenBucketRateLimiter(1, 0)
        assert False, "expected ValueError for invalid refill_rate"
    except ValueError:
        pass
