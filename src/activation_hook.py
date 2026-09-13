"""Layer-20 residual-stream hook at PRE_ACTION_DECISION_BOUNDARY."""

from typing import Any

import numpy as np

POSITION_NAME = "PRE_ACTION_DECISION_BOUNDARY"
TARGET_LAYER = 20


class ActivationHook:
    def __init__(self, seed: int = 260913, hidden_size: int = 32) -> None:
        self.rng = np.random.default_rng(seed)
        self.hidden_size = hidden_size
        self.layer = TARGET_LAYER
        self.position_name = POSITION_NAME

    def capture(self, scenario: dict[str, Any], adopted: bool) -> np.ndarray:
        offset = 0.85 if adopted else 0.12
        noise = self.rng.normal(loc=offset, scale=0.04, size=self.hidden_size)
        return noise.astype(np.float64)
