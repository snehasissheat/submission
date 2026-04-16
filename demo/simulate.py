from src.main import TokenBucketRateLimiter

def run_demo():
    limiter = TokenBucketRateLimiter(100, 10)
    cid = "stripe-test"

    print("T=0 → 60 requests")
    for i in range(60):
        print(limiter.check(cid, 0))

    print("\nT=2000ms → 70 requests")
    for i in range(70):
        print(limiter.check(cid, 2000))

    print("\nT=7000ms → 30 requests")
    for i in range(30):
        print(limiter.check(cid, 7000))


if __name__ == "__main__":
    run_demo()