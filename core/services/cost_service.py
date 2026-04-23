from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from core.models.cost import Cost, CostCreate, CostType, CostUpdate
from core.domain.money import to_money
from data.repositories.cost_repository import CostRepository


class CostService:
    """Application service for fixed and variable costs."""

    def __init__(self, repository: CostRepository) -> None:
        self.repository = repository

    def create_cost(
        self,
        name: str,
        amount: float,
        cost_type: str,
    ) -> Cost:
        payload = CostCreate(
            name=name.strip(),
            amount=to_money(amount),
            cost_type=self._parse_cost_type(cost_type),
            recorded_at=datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds"),
        )
        self._validate_name(payload.name)
        self._validate_positive_value(payload.amount)
        return self.repository.create(payload)

    def update_cost(
        self,
        cost_id: int,
        *,
        name: str | None = None,
        amount: float | None = None,
        cost_type: str | None = None,
    ) -> Cost:
        payload = CostUpdate(
            name=name.strip() if name is not None else None,
            amount=to_money(amount) if amount is not None else None,
            cost_type=self._parse_cost_type(cost_type) if cost_type is not None else None,
        )
        if payload.name is not None:
            self._validate_name(payload.name)
        if payload.amount is not None:
            self._validate_positive_value(payload.amount)
        return self.repository.update(cost_id, payload)

    def get_cost(self, cost_id: int) -> Cost:
        return self.repository.get_by_id(cost_id)

    def filter_costs(
        self,
        *,
        name: str | None = None,
        cost_type: str | None = None,
        min_amount: Decimal | float | int | str | None = None,
        max_amount: Decimal | float | int | str | None = None,
    ) -> list[Cost]:
        filters: dict[str, Any] = {}
        if name:
            filters["name"] = name.strip()
        if cost_type:
            filters["cost_type"] = self._parse_cost_type(cost_type)
        if min_amount is not None:
            filters["min_amount"] = to_money(min_amount)
        if max_amount is not None:
            filters["max_amount"] = to_money(max_amount)
        return self.repository.filter(filters)

    def delete_cost(self, cost_id: int) -> None:
        self.repository.delete(cost_id)

    @staticmethod
    def _parse_cost_type(value: str) -> CostType:
        normalized = value.strip().lower()
        try:
            return CostType(normalized)
        except ValueError as error:
            raise ValueError("Cost type must be 'fixed' or 'variable'.") from error

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name:
            raise ValueError("Cost name cannot be empty.")

    @staticmethod
    def _validate_positive_value(amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("Cost amount must be greater than zero.")
