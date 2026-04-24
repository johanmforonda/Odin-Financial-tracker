from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from backend.core.domain.cost_calculator import calculate_total_variable_cost
from backend.core.domain.pricing import (
    calculate_margin,
    calculate_recommended_price,
    round_recommended_price,
)
from backend.core.models.cost import CostType
from backend.core.models.product import Product
from backend.data.repositories.cost_repository import CostRepository
from backend.data.repositories.product_repository import ProductRepository


class PricingService:
    """Calculation-focused service for pricing recommendations."""

    def __init__(
        self,
        product_repository: ProductRepository,
        cost_repository: CostRepository,
    ) -> None:
        self.product_repository = product_repository
        self.cost_repository = cost_repository

    def calculate_margin(self, minimum_revenue: Decimal | float | int | str) -> Decimal:
        current_month = datetime.now(UTC).strftime("%Y-%m")
        fixed_costs = sum(
            (cost.amount for cost in self.cost_repository.filter(
                {
                    "cost_type": CostType.FIXED,
                    "recorded_at_from": f"{current_month}-01T00:00:00",
                    "recorded_at_to": self._build_next_month_start(current_month),
                }
            )),
            start=Decimal("0.00"),
        )
        return calculate_margin(fixed_costs, minimum_revenue)

    def recommend_price(
        self,
        product_id: int,
        minimum_revenue: Decimal | float | int | str,
    ) -> Product:
        product = self.product_repository.get_by_id(product_id)
        variable_costs = self.product_repository.list_variable_costs(product_id)
        total_variable_cost = calculate_total_variable_cost(cost.amount for cost in variable_costs)
        margin = self.calculate_margin(minimum_revenue)
        recommended_price = round_recommended_price(
            calculate_recommended_price(total_variable_cost, margin)
        )
        sale_price = product.sale_price or recommended_price
        self.product_repository.update_prices(
            product_id=product_id,
            cost_price=total_variable_cost,
            recommended_price=recommended_price,
            sale_price=sale_price,
        )
        return self.product_repository.get_by_id(product_id)

    def recommend_prices(
        self,
        minimum_revenue: Decimal | float | int | str,
    ) -> list[Product]:
        products = self.product_repository.filter({})
        return [self.recommend_price(product.id, minimum_revenue) for product in products]

    @staticmethod
    def _build_next_month_start(month: str) -> str:
        current = datetime.strptime(month, "%Y-%m")
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1)
        else:
            next_month = current.replace(month=current.month + 1)
        return next_month.isoformat(timespec="seconds")
