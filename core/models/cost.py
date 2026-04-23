from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class CostType(StrEnum):
    FIXED = "fixed"
    VARIABLE = "variable"


@dataclass(slots=True)
class Cost:
    id: int
    name: str
    amount: Decimal
    cost_type: CostType
    recorded_at: str


@dataclass(slots=True)
class CostCreate:
    name: str
    amount: Decimal
    cost_type: CostType
    recorded_at: str


@dataclass(slots=True)
class CostUpdate:
    name: str | None = None
    amount: Decimal | None = None
    cost_type: CostType | None = None
    recorded_at: str | None = None
