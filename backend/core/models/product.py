from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class Product:
    id: int
    name: str
    cost_price: Decimal
    recommended_price: Decimal
    sale_price: Decimal


@dataclass(slots=True)
class ProductCreate:
    name: str
    sale_price: Decimal | None = None


@dataclass(slots=True)
class ProductUpdate:
    name: str | None = None
    sale_price: Decimal | None = None
