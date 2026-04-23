from __future__ import annotations

from decimal import Decimal

from .money import to_money


def calculate_margin(
    fixed_costs: Decimal | float | int | str,
    minimum_revenue: Decimal | float | int | str,
) -> Decimal:
    fixed_costs_value = to_money(fixed_costs)
    minimum_revenue_value = to_money(minimum_revenue)
    if minimum_revenue_value <= 0:
        raise ValueError("Minimum revenue must be greater than zero.")
    margin = fixed_costs_value / minimum_revenue_value
    if margin >= 1:
        raise ValueError("Margin must be lower than 1. Increase minimum revenue or reduce fixed costs.")
    return to_money(margin)


def calculate_recommended_price(
    variable_costs: Decimal | float | int | str,
    margin: Decimal | float | int | str,
) -> Decimal:
    variable_costs_value = to_money(variable_costs)
    margin_value = to_money(margin)
    if margin_value >= 1:
        raise ValueError("Margin must be lower than 1.")
    raw_price = variable_costs_value / (Decimal("1") - margin_value)
    return to_money(raw_price)


def round_recommended_price(value: Decimal | float | int | str) -> Decimal:
    return to_money(value)
