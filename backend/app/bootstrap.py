from __future__ import annotations

from backend.core.stats import StatsService
from backend.core.services.cost_service import CostService
from backend.core.services.pricing_service import PricingService
from backend.core.services.product_service import ProductService
from backend.core.services.sales_service import SalesService
from backend.data.database import DatabaseManager
from backend.data.repositories.cost_repository import CostRepository
from backend.data.repositories.product_repository import ProductRepository
from backend.data.repositories.sales_repository import SalesRepository
from backend.data.repositories.stats_repository import StatsRepository


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
