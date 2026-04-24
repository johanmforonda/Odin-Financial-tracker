from __future__ import annotations

from decimal import Decimal

from .money import to_money


def calculate_total_income(amount: Decimal | float | int | str) -> Decimal:
    return to_money(amount)


def calculate_total_margin(
    total_income: Decimal | float | int | str,
    total_variable_costs: Decimal | float | int | str,
) -> Decimal:
    return to_money(Decimal(str(total_income)) - Decimal(str(total_variable_costs)))


def calculate_profitability(
    total_income: Decimal | float | int | str,
    total_variable_costs: Decimal | float | int | str,
    total_fixed_costs: Decimal | float | int | str,
) -> Decimal:
    return to_money(
        Decimal(str(total_income))
        - Decimal(str(total_variable_costs))
        - Decimal(str(total_fixed_costs))
    )


def calculate_fixed_cost_coverage(
    total_margin: Decimal | float | int | str,
    total_fixed_costs: Decimal | float | int | str,
) -> tuple[Decimal, Decimal, Decimal]:
    margin_value = to_money(total_margin)
    fixed_costs_value = to_money(total_fixed_costs)
    covered_amount = min(max(margin_value, Decimal("0.00")), fixed_costs_value)
    uncovered_amount = max(fixed_costs_value - covered_amount, Decimal("0.00"))
    if fixed_costs_value == 0:
        coverage_percentage = Decimal("100.00")
    else:
        coverage_percentage = to_money((covered_amount / fixed_costs_value) * Decimal("100"))
    return (
        to_money(covered_amount),
        to_money(uncovered_amount),
        coverage_percentage,
    )


def calculate_profitability_evolution(
    current_profitability: Decimal | float | int | str,
    previous_profitability: Decimal | float | int | str,
) -> tuple[Decimal, Decimal | None]:
    current_value = to_money(current_profitability)
    previous_value = to_money(previous_profitability)
    absolute_change = to_money(current_value - previous_value)
    if previous_value == 0:
        percentage_change = None
    else:
        percentage_change = to_money((absolute_change / abs(previous_value)) * Decimal("100"))
    return absolute_change, percentage_change
