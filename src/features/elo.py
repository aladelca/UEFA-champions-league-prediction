from dataclasses import dataclass


@dataclass
class EloConfig:
    k_factor: float = 20.0
    base_rating: float = 1500.0


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
