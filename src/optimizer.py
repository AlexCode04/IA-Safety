"""Uniform versus risk-weighted adaptive allocation under one budget."""

from typing import Any


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
