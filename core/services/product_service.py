from __future__ import annotations

from decimal import Decimal
from typing import Any

from core.domain.money import to_money
from core.models.product import Product, ProductCreate, ProductUpdate
from data.repositories.cost_repository import CostRepository
from data.repositories.product_repository import ProductRepository


class ProductService:
    """Application service for product management."""

    def __init__(
        self,
        repository: ProductRepository,
        cost_repository: CostRepository,
    ) -> None:
        self.repository = repository
        self.cost_repository = cost_repository

    def create_product(
        self,
        name: str,
        sale_price: Decimal | float | int | str | None = None,
    ) -> Product:
        payload = ProductCreate(
            name=name.strip(),
            sale_price=to_money(sale_price) if sale_price is not None else None,
        )
        self._validate_name(payload.name)
        if payload.sale_price is not None:
            self._validate_positive_value(payload.sale_price, "sale_price")
        return self.repository.create(payload)

    def update_product(
        self,
        product_id: int,
        *,
        name: str | None = None,
        sale_price: Decimal | float | int | str | None = None,
    ) -> Product:
        payload = ProductUpdate(
            name=name.strip() if name is not None else None,
            sale_price=to_money(sale_price) if sale_price is not None else None,
        )
        if payload.name is not None:
            self._validate_name(payload.name)
        if payload.sale_price is not None:
            self._validate_positive_value(payload.sale_price, "sale_price")
        return self.repository.update(product_id, payload)

    def get_product(self, product_id: int) -> Product:
        return self.repository.get_by_id(product_id)

    def search_products(self, term: str) -> list[Product]:
        return self.repository.search_by_name(term.strip())

    def filter_products(
        self,
        *,
        name: str | None = None,
        min_cost_price: Decimal | float | int | str | None = None,
        max_cost_price: Decimal | float | int | str | None = None,
        min_recommended_price: Decimal | float | int | str | None = None,
        max_recommended_price: Decimal | float | int | str | None = None,
        min_sale_price: Decimal | float | int | str | None = None,
        max_sale_price: Decimal | float | int | str | None = None,
    ) -> list[Product]:
        filters: dict[str, Any] = {}
        if name:
            filters["name"] = name.strip()

        numeric_filters = {
            "min_cost_price": min_cost_price,
            "max_cost_price": max_cost_price,
            "min_recommended_price": min_recommended_price,
            "max_recommended_price": max_recommended_price,
            "min_sale_price": min_sale_price,
            "max_sale_price": max_sale_price,
        }
        for key, value in numeric_filters.items():
            if value is not None:
                filters[key] = to_money(value)

        return self.repository.filter(filters)

    def add_variable_cost(self, product_id: int, cost_id: int) -> Product:
        cost = self.cost_repository.get_by_id(cost_id)
        if cost.cost_type.value != "variable":
            raise ValueError("Only variable costs can be assigned to products.")
        self.repository.add_variable_cost(product_id, cost_id)
        return self.repository.get_by_id(product_id)

    def remove_variable_cost(self, product_id: int, cost_id: int) -> Product:
        self.repository.remove_variable_cost(product_id, cost_id)
        return self.repository.get_by_id(product_id)

    def list_variable_costs(self, product_id: int):
        return self.repository.list_variable_costs(product_id)

    def delete_product(self, product_id: int) -> None:
        self.repository.delete(product_id)

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name:
            raise ValueError("Product name cannot be empty.")

    @staticmethod
    def _validate_positive_value(value: Decimal, field_name: str) -> None:
        if value <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")
