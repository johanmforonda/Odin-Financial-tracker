from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from .money import to_money


def calculate_total_variable_cost(amounts: Iterable[Decimal | float | int | str]) -> Decimal:
    total = sum((Decimal(str(amount)) for amount in amounts), start=Decimal("0"))
    return to_money(total)
