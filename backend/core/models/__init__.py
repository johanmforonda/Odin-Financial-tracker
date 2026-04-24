"""Domain models for Odin services."""

from .cost import Cost, CostCreate, CostType, CostUpdate
from .product import Product, ProductCreate, ProductUpdate
from .sale import Sale, SaleCreate, SaleUpdate
from .stats import FixedCostCoverage, MonthlyStats, ProfitabilityEvolution

__all__ = [
    "Cost",
    "CostCreate",
    "CostType",
    "CostUpdate",
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "Sale",
    "SaleCreate",
    "SaleUpdate",
    "FixedCostCoverage",
    "MonthlyStats",
    "ProfitabilityEvolution",
]
