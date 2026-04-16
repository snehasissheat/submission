import math
from dataclasses import dataclass
from typing import Dict

from src.types import Decision
from src.utils import min_cap


@dataclass
class BucketState:
    tokens: float
    last_refill_ms: int


class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")

        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.buckets: Dict[str, BucketState] = {}

    def _refill(self, customer_id: str, current_time_ms: int) -> None:
        state = self.buckets[customer_id]
        elapsed_ms = max(0, current_time_ms - state.last_refill_ms)
        tokens_to_add = (elapsed_ms / 1000.0) * self.refill_rate

        state.tokens = min_cap(state.tokens + tokens_to_add, self.capacity)
        state.last_refill_ms = max(state.last_refill_ms, current_time_ms)

    def check(self, customer_id: str, current_time_ms: int) -> Decision:
        if customer_id not in self.buckets:
            self.buckets[customer_id] = BucketState(
                tokens=float(self.capacity),
                last_refill_ms=current_time_ms,
            )

        self._refill(customer_id, current_time_ms)

        state = self.buckets[customer_id]
        if state.tokens >= 1 - 1e-9:
            state.tokens = max(0.0, state.tokens - 1.0)
            return Decision(
                allowed=True,
                remaining=int(state.tokens),
                retry_after_ms=0,
            )

        tokens_needed = 1.0 - state.tokens
        retry_after_seconds = tokens_needed / self.refill_rate
        retry_after_ms = math.ceil(retry_after_seconds * 1000)
        return Decision(
            allowed=False,
            remaining=0,
            retry_after_ms=retry_after_ms,
        )
