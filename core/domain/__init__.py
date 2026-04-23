"""Pure domain logic for Odin."""

from .money import to_money
from .cost_calculator import calculate_total_variable_cost
from .pricing import (
    calculate_margin,
    calculate_recommended_price,
    round_recommended_price,
)
from .stats import (
    calculate_fixed_cost_coverage,
    calculate_profitability,
    calculate_profitability_evolution,
    calculate_total_income,
    calculate_total_margin,
)

__all__ = [
    "to_money",
    "calculate_total_variable_cost",
    "calculate_margin",
    "calculate_recommended_price",
    "round_recommended_price",
    "calculate_fixed_cost_coverage",
    "calculate_profitability",
    "calculate_profitability_evolution",
    "calculate_total_income",
    "calculate_total_margin",
]
