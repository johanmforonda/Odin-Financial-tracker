from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class FixedCostCoverage:
    covered_amount: Decimal
    uncovered_amount: Decimal
    coverage_percentage: Decimal


@dataclass(slots=True)
class ProfitabilityEvolution:
    current_profitability: Decimal
    previous_profitability: Decimal
    absolute_change: Decimal
    percentage_change: Decimal | None


@dataclass(slots=True)
class MonthlyStats:
    month: str
    total_fixed_costs: Decimal
    total_variable_costs: Decimal
    total_income: Decimal
    total_margin: Decimal
    profitability: Decimal
    fixed_cost_coverage: FixedCostCoverage
    profitability_evolution: ProfitabilityEvolution
