"""Frozen seeds from EXPERIMENT_SPEC.md section 15."""

import random

import numpy as np


def apply_seeds(python_seed: int, numpy_seed: int) -> None:
    random.seed(python_seed)
    np.random.seed(numpy_seed)
