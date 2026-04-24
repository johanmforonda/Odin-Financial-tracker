from __future__ import annotations

from core.stats import StatsService
from core.services.cost_service import CostService
from core.services.pricing_service import PricingService
from core.services.product_service import ProductService
from core.services.sales_service import SalesService
from data.database import DatabaseManager
from data.repositories.cost_repository import CostRepository
from data.repositories.product_repository import ProductRepository
from data.repositories.sales_repository import SalesRepository
from data.repositories.stats_repository import StatsRepository


def build_services() -> tuple[ProductService, CostService, PricingService, SalesService, StatsService]:
    database = DatabaseManager()
    database.initialize()
    product_repository = ProductRepository(database)
    cost_repository = CostRepository(database)
    sales_repository = SalesRepository(database)
    stats_repository = StatsRepository(database)
    return (
        ProductService(product_repository, cost_repository),
        CostService(cost_repository),
        PricingService(product_repository, cost_repository),
        SalesService(sales_repository, product_repository),
        StatsService(stats_repository),
    )
