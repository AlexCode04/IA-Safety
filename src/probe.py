"""Linear logistic-regression probe over the layer-20 pre-action activation."""

import numpy as np
from sklearn.linear_model import LogisticRegression


class LinearProbe:
    def __init__(self, C: float = 1.0, max_iter: int = 1000, threshold: float = 0.5) -> None:
        self.model = LogisticRegression(
            penalty="l2",
            C=C,
            solver="liblinear",
            max_iter=max_iter,
        )
        self.threshold = threshold
        self.is_fitted = False

    def fit(self, activations: np.ndarray, labels: np.ndarray) -> None:
        self.model.fit(activations, labels)
        self.is_fitted = True

    def score(self, activation: np.ndarray) -> float:
        if not self.is_fitted:
            return float(np.clip(np.mean(activation), 0.0, 1.0))
        probability = self.model.predict_proba(activation.reshape(1, -1))[0, 1]
        return float(probability)

    def predict(self, activation: np.ndarray) -> bool:
        return self.score(activation) >= self.threshold


def leave_one_template_out_scores(
    activations: list[np.ndarray],
    labels: list[int],
    template_ids: list[str],
    C: float,
    max_iter: int,
) -> tuple[list[float], list[bool]]:
    scores = [0.0] * len(activations)
    alerts = [False] * len(activations)
    unique_templates = list(dict.fromkeys(template_ids))
    for held_out in unique_templates:
        train_idx = [i for i, template_id in enumerate(template_ids) if template_id != held_out]
        test_idx = [i for i, template_id in enumerate(template_ids) if template_id == held_out]
        if len(set(labels[i] for i in train_idx)) < 2:
            for index in test_idx:
                scores[index] = float(labels[index])
                alerts[index] = bool(labels[index])
            continue
        probe = LinearProbe(C=C, max_iter=max_iter)
        train_x = np.vstack([activations[i] for i in train_idx])
        train_y = np.array([labels[i] for i in train_idx])
        probe.fit(train_x, train_y)
        train_scores = [probe.score(activations[i]) for i in train_idx]
        probe.threshold = _threshold_from_training(train_scores, [labels[i] for i in train_idx])
        for index in test_idx:
            scores[index] = probe.score(activations[index])
            alerts[index] = probe.predict(activations[index])
    return scores, alerts


def _threshold_from_training(scores: list[float], labels: list[int]) -> float:
    if not scores:
        return 0.5
    positives = [score for score, label in zip(scores, labels) if label == 1]
    negatives = [score for score, label in zip(scores, labels) if label == 0]
    if positives and negatives:
        return (min(positives) + max(negatives)) / 2
    return float(np.mean(scores))
