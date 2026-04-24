from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from backend.core.domain.money import to_money
from backend.core.models.sale import Sale, SaleCreate, SaleUpdate
from backend.data.repositories.product_repository import ProductRepository
from backend.data.repositories.sales_repository import SalesRepository


class SalesService:
    """Application service for product sales records."""

    def __init__(
        self,
        repository: SalesRepository,
        product_repository: ProductRepository,
    ) -> None:
        self.repository = repository
        self.product_repository = product_repository

    def create_sale(
        self,
        product_id: int,
        *,
        sale_price: Decimal | float | int | str | None = None,
        sale_date: str | None = None,
    ) -> Sale:
        product = self.product_repository.get_by_id(product_id)
        variable_costs = self.product_repository.list_variable_costs(product_id)
        selected_sale_price = (
            to_money(sale_price) if sale_price is not None else product.sale_price
        )
        self._validate_positive_value(selected_sale_price, "sale_price")
        selected_sale_date = sale_date or self._build_sale_date()
        payload = SaleCreate(
            product_id=product.id,
            product_name=product.name,
            sale_price=selected_sale_price,
            sale_date=selected_sale_date,
        )
        return self.repository.create(
            payload,
            variable_cost_snapshots=[
                {
                    "cost_id": cost.id,
                    "cost_name": cost.name,
                    "amount": cost.amount,
                    "sale_date": selected_sale_date,
                }
                for cost in variable_costs
            ],
        )

    def update_sale(
        self,
        sale_id: int,
        *,
        sale_price: Decimal | float | int | str | None = None,
        sale_date: str | None = None,
    ) -> Sale:
        payload = SaleUpdate(
            sale_price=to_money(sale_price) if sale_price is not None else None,
            sale_date=sale_date,
        )
        if payload.sale_price is not None:
            self._validate_positive_value(payload.sale_price, "sale_price")
        return self.repository.update(sale_id, payload)

    def get_sale(self, sale_id: int) -> Sale:
        return self.repository.get_by_id(sale_id)

    def filter_sales(
        self,
        *,
        product_id: int | None = None,
        product_name: str | None = None,
        sale_date: str | None = None,
        min_sale_price: Decimal | float | int | str | None = None,
        max_sale_price: Decimal | float | int | str | None = None,
    ) -> list[Sale]:
        filters: dict[str, Any] = {}
        if product_id is not None:
            filters["product_id"] = product_id
        if product_name:
            filters["product_name"] = product_name.strip()
        if sale_date:
            filters["sale_date"] = sale_date.strip()
        if min_sale_price is not None:
            filters["min_sale_price"] = to_money(min_sale_price)
        if max_sale_price is not None:
            filters["max_sale_price"] = to_money(max_sale_price)
        return self.repository.filter(filters)

    def delete_sale(self, sale_id: int) -> None:
        self.repository.delete(sale_id)

    @staticmethod
    def _build_sale_date() -> str:
        return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")

    @staticmethod
    def _validate_positive_value(value: Decimal, field_name: str) -> None:
        if value <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")
