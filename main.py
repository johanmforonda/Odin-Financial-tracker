from __future__ import annotations

from core.stats import StatsService
from core.services.cost_service import CostService
from core.services.pricing_service import PricingService
from core.services.product_service import ProductService
from core.services.sales_service import SalesService
from data.repositories.cost_repository import CostRepository
from data.database import DatabaseManager
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


if __name__ == "__main__":
    product_service, cost_service, pricing_service, sales_service, stats_service = build_services()

    coffee = product_service.create_product(name="Premium Coffee")
    cup = cost_service.create_cost(name="Cup", amount=600, cost_type="variable")
    beans = cost_service.create_cost(name="Coffee Beans", amount=2200, cost_type="variable")
    rent = cost_service.create_cost(name="Monthly Rent", amount=3000000, cost_type="fixed")

    product_service.add_variable_cost(coffee.id, cup.id)
    product_service.add_variable_cost(coffee.id, beans.id)
    priced_product = pricing_service.recommend_price(coffee.id, minimum_revenue=100000000)
    updated_product = product_service.update_product(coffee.id, sale_price=3800)
    sale = sales_service.create_sale(coffee.id)

    print("Created product:", coffee)
    print("Recommended product:", priced_product)
    print("Updated product:", updated_product)
    print("Created sale:", sale)
    print("Product variable costs:", product_service.list_variable_costs(coffee.id))
    print("Search product:", product_service.search_products("Coffee"))
    print("Filter products:", product_service.filter_products(min_recommended_price=3000))
    print("Filter variable costs:", cost_service.filter_costs(cost_type="variable"))
    print("Filter fixed costs:", cost_service.filter_costs(cost_type="fixed"))
    print("Filter sales:", sales_service.filter_sales(product_name="Coffee"))
    print("Current month stats:", stats_service.get_monthly_stats_as_dict())
    print("Sample fixed cost:", rent)
