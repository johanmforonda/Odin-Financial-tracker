from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class Sale:
    id: int
    product_id: int
    product_name: str
    sale_price: Decimal
    sale_date: str


@dataclass(slots=True)
class SaleCreate:
    product_id: int
    product_name: str
    sale_price: Decimal
    sale_date: str


@dataclass(slots=True)
class SaleUpdate:
    sale_price: Decimal | None = None
    sale_date: str | None = None
