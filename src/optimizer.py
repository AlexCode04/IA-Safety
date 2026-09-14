"""Uniform versus risk-weighted adaptive allocation under one budget."""

from typing import Any

try:
    from scipy.optimize import linprog
    scipy_available = True
except ImportError:  # pragma: no cover - fallback when scipy is absent
    linprog = None
    scipy_available = False

POLICY_PRIORITY: dict[str, list[list[str]]] = {
    "baseline": [],
    "action_only": [["observable"]],
    "nla_probe_cot": [["observable", "nla"], ["observable", "probe"], ["observable"]],
    "probe_nla_cot": [["observable", "probe", "nla"], ["observable", "probe"], ["observable"]],
    "cot_nla": [["observable", "cot", "nla"], ["observable", "cot"], ["observable"]],
}


class BudgetOptimizer:
    def __init__(self, assumed_costs: dict[str, float], budget_limit: float, uniform_views: list[str]) -> None:
        self.assumed_costs = assumed_costs
        self.budget_limit = budget_limit
        self.uniform_views = list(uniform_views)

    def cost_of(self, views: list[str]) -> float:
        return sum(self.assumed_costs[view] for view in views)

    def select_uniform(self, _scenario: dict[str, Any]) -> list[str]:
        return list(self.uniform_views)

    def plan_adaptive(self, scenarios: list[dict[str, Any]]) -> dict[str, list[str]]:
        remaining = self.budget_limit
        ranked = sorted(scenarios, key=lambda item: float(item["severity"]), reverse=True)
        assigned: dict[str, list[str]] = {}
        for scenario in ranked:
            if float(scenario["severity"]) >= 3.0 and remaining >= self.cost_of(["observable", "nla"]):
                views = ["observable", "nla"]
            elif remaining >= self.cost_of(["observable", "probe"]):
                views = ["observable", "probe"]
            elif remaining >= self.assumed_costs["observable"]:
                views = ["observable"]
            else:
                views = []
            assigned[scenario["id"]] = views
            remaining -= self.cost_of(views)
        return assigned

    def plan_policies(self, scenarios: list[dict[str, Any]]) -> dict[str, dict[str, list[str]]]:
        plans: dict[str, dict[str, list[str]]] = {}
        for kind, priority in POLICY_PRIORITY.items():
            if kind == "baseline":
                plans[kind] = {scenario["id"]: self.select_uniform(scenario) for scenario in scenarios}
                continue
            remaining = self.budget_limit
            ranked = sorted(scenarios, key=lambda item: float(item["severity"]), reverse=True)
            assigned: dict[str, list[str]] = {}
            for scenario in ranked:
                views: list[str] = []
                for candidate in priority:
                    if remaining >= self.cost_of(candidate):
                        views = candidate
                        break
                assigned[scenario["id"]] = views
                remaining -= self.cost_of(views)
            plans[kind] = assigned
        return plans

    def canonical_views(self, kind: str) -> list[str]:
        if kind == "baseline":
            return list(self.uniform_views)
        priority = POLICY_PRIORITY.get(kind, [])
        return list(priority[0]) if priority else []

    def plan_lp(self, scenarios: list[dict[str, Any]], benefits: dict[str, dict[str, float]]) -> dict[str, str]:
        if not scipy_available:
            return {scenario["id"]: "baseline" for scenario in scenarios}
        kinds = sorted(POLICY_PRIORITY)
        ids = [scenario["id"] for scenario in scenarios]
        var_index = {f"{sid}::{kind}": i for i, (sid, kind) in enumerate((sid, k) for sid in ids for k in kinds)}
        c = [-benefits.get(sid, {}).get(kind, 0.0) for sid in ids for kind in kinds]
        a_eq = [[1.0 if i // len(kinds) == row else 0.0 for i in range(len(c))] for row in range(len(ids))]
        b_eq = [1.0] * len(ids)
        a_ub = [[self.cost_of(self.canonical_views(kind)) for sid in ids for kind in kinds]]
        b_ub = [self.budget_limit]
        result = linprog(c, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=b_eq, bounds=(0, 1), method="highs")
        if not result.success:
            return {scenario["id"]: "baseline" for scenario in scenarios}
        assignment: dict[str, str] = {}
        for sid in ids:
            best_kind = max(kinds, key=lambda kind: result.x[var_index[f"{sid}::{kind}"]])
            assignment[sid] = best_kind
        candidates = {sid: assignment[sid] for sid in ids}
        while sum(self.cost_of(self.canonical_views(kind)) for kind in candidates.values()) > self.budget_limit + 1e-9:
            sid = min(
                candidates,
                key=lambda s: benefits.get(s, {}).get(candidates[s], 0.0)
                / max(self.cost_of(self.canonical_views(candidates[s])), 1e-9),
            )
            candidates[sid] = "action_only"
        return candidates
