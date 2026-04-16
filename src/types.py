from dataclasses import dataclass

@dataclass
class Decision:
    allowed: bool
    remaining: int
    retry_after_ms: int