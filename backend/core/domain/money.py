from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")
WHOLE_UNIT = Decimal("1")


def to_money(value: Decimal | float | int | str) -> Decimal:
    """Normalize numeric values to a money-friendly Decimal."""
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def round_up_to_whole(value: Decimal | float | int | str) -> Decimal:
    """Round prices up to the next whole unit to avoid awkward decimals."""
    return Decimal(str(value)).quantize(WHOLE_UNIT, rounding=ROUND_CEILING)
