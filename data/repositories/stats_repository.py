from __future__ import annotations

from decimal import Decimal

from ..database import DatabaseManager


class StatsRepository:
    """Aggregate queries used by the statistics service."""

    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def get_total_fixed_costs(self, start_date: str, end_date: str) -> Decimal:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(CAST(amount AS REAL)), 0) AS total_fixed_costs
                FROM costs
                WHERE cost_type = 'fixed'
                  AND recorded_at >= ?
                  AND recorded_at < ?
                """,
                (start_date, end_date),
            ).fetchone()
        return Decimal(str(row["total_fixed_costs"])).quantize(Decimal("0.01"))

    def get_total_variable_costs(self, start_date: str, end_date: str) -> Decimal:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(CAST(amount AS REAL)), 0) AS total_variable_costs
                FROM sale_variable_costs
                WHERE sale_date >= ?
                  AND sale_date < ?
                """,
                (start_date, end_date),
            ).fetchone()
        return Decimal(str(row["total_variable_costs"])).quantize(Decimal("0.01"))

    def get_total_income(self, start_date: str, end_date: str) -> Decimal:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(CAST(sale_price AS REAL)), 0) AS total_income
                FROM sales
                WHERE sale_date >= ?
                  AND sale_date < ?
                """,
                (start_date, end_date),
            ).fetchone()
        return Decimal(str(row["total_income"])).quantize(Decimal("0.01"))
