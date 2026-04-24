from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal

from backend.core.domain.stats import (
    calculate_fixed_cost_coverage,
    calculate_profitability,
    calculate_profitability_evolution,
    calculate_total_income,
    calculate_total_margin,
)
from backend.core.models.stats import FixedCostCoverage, MonthlyStats, ProfitabilityEvolution
from backend.data.repositories.stats_repository import StatsRepository


class StatsService:
    """Monthly business statistics service."""

    def __init__(self, repository: StatsRepository) -> None:
        self.repository = repository

    def get_total_fixed_costs(self, month: str | None = None) -> Decimal:
        start_date, end_date, _ = self._resolve_month_range(month)
        return self.repository.get_total_fixed_costs(start_date, end_date)

    def get_total_variable_costs(self, month: str | None = None) -> Decimal:
        start_date, end_date, _ = self._resolve_month_range(month)
        return self.repository.get_total_variable_costs(start_date, end_date)

    def get_total_income(self, month: str | None = None) -> Decimal:
        start_date, end_date, _ = self._resolve_month_range(month)
        income = self.repository.get_total_income(start_date, end_date)
        return calculate_total_income(income)

    def get_total_margin(self, month: str | None = None) -> Decimal:
        total_income = self.get_total_income(month)
        total_variable_costs = self.get_total_variable_costs(month)
        return calculate_total_margin(total_income, total_variable_costs)

    def get_profitability(self, month: str | None = None) -> Decimal:
        total_income = self.get_total_income(month)
        total_variable_costs = self.get_total_variable_costs(month)
        total_fixed_costs = self.get_total_fixed_costs(month)
        return calculate_profitability(total_income, total_variable_costs, total_fixed_costs)

    def get_fixed_cost_coverage(self, month: str | None = None) -> FixedCostCoverage:
        total_margin = self.get_total_margin(month)
        total_fixed_costs = self.get_total_fixed_costs(month)
        covered_amount, uncovered_amount, coverage_percentage = calculate_fixed_cost_coverage(
            total_margin,
            total_fixed_costs,
        )
        return FixedCostCoverage(
            covered_amount=covered_amount,
            uncovered_amount=uncovered_amount,
            coverage_percentage=coverage_percentage,
        )

    def get_profitability_evolution(
        self,
        month: str | None = None,
    ) -> ProfitabilityEvolution:
        _, _, resolved_month = self._resolve_month_range(month)
        previous_month = self._get_previous_month(resolved_month)
        current_profitability = self.get_profitability(resolved_month)
        previous_profitability = self.get_profitability(previous_month)
        absolute_change, percentage_change = calculate_profitability_evolution(
            current_profitability,
            previous_profitability,
        )
        return ProfitabilityEvolution(
            current_profitability=current_profitability,
            previous_profitability=previous_profitability,
            absolute_change=absolute_change,
            percentage_change=percentage_change,
        )

    def get_monthly_stats(self, month: str | None = None) -> MonthlyStats:
        _, _, resolved_month = self._resolve_month_range(month)
        total_fixed_costs = self.get_total_fixed_costs(resolved_month)
        total_variable_costs = self.get_total_variable_costs(resolved_month)
        total_income = self.get_total_income(resolved_month)
        total_margin = calculate_total_margin(total_income, total_variable_costs)
        profitability = calculate_profitability(
            total_income,
            total_variable_costs,
            total_fixed_costs,
        )
        return MonthlyStats(
            month=resolved_month,
            total_fixed_costs=total_fixed_costs,
            total_variable_costs=total_variable_costs,
            total_income=total_income,
            total_margin=total_margin,
            profitability=profitability,
            fixed_cost_coverage=self.get_fixed_cost_coverage(resolved_month),
            profitability_evolution=self.get_profitability_evolution(resolved_month),
        )

    def get_monthly_stats_as_dict(self, month: str | None = None) -> dict[str, object]:
        return asdict(self.get_monthly_stats(month))

    def get_profitability_series(
        self,
        month: str | None = None,
        periods: int = 6,
    ) -> list[dict[str, Decimal | str | None]]:
        _, _, resolved_month = self._resolve_month_range(month)
        current = datetime.strptime(resolved_month, "%Y-%m")
        months: list[str] = []
        cursor = current

        for _ in range(periods):
            months.append(cursor.strftime("%Y-%m"))
            if cursor.month == 1:
                cursor = cursor.replace(year=cursor.year - 1, month=12)
            else:
                cursor = cursor.replace(month=cursor.month - 1)

        series: list[dict[str, Decimal | str | None]] = []
        for item in reversed(months):
            profitability = self.get_profitability(item)
            series.append(
                {
                    "month": item,
                    "profitability": profitability,
                }
            )
        return series

    @staticmethod
    def _resolve_month_range(month: str | None) -> tuple[str, str, str]:
        if month is None:
            current_date = datetime.now(UTC).replace(tzinfo=None)
            resolved_month = current_date.strftime("%Y-%m")
            start_date = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = datetime.strptime(month, "%Y-%m")
            resolved_month = month

        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)

        return (
            start_date.isoformat(timespec="seconds"),
            end_date.isoformat(timespec="seconds"),
            resolved_month,
        )

    @staticmethod
    def _get_previous_month(month: str) -> str:
        current = datetime.strptime(month, "%Y-%m")
        if current.month == 1:
            previous = current.replace(year=current.year - 1, month=12)
        else:
            previous = current.replace(month=current.month - 1)
        return previous.strftime("%Y-%m")
