from __future__ import annotations

from decimal import Decimal

from backend.core.models.cost import Cost, CostCreate, CostType, CostUpdate

from ..database import DatabaseManager


class CostRepository:
    """Persistence layer for costs."""

    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def create(self, payload: CostCreate) -> Cost:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO costs (name, amount, cost_type, recorded_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    payload.name,
                    str(payload.amount),
                    payload.cost_type.value,
                    payload.recorded_at,
                ),
            )
            connection.commit()
            return self.get_by_id(cursor.lastrowid)

    def update(self, cost_id: int, payload: CostUpdate) -> Cost:
        current_cost = self.get_by_id(cost_id)
        name = payload.name if payload.name is not None else current_cost.name
        amount = payload.amount if payload.amount is not None else current_cost.amount
        cost_type = (
            payload.cost_type if payload.cost_type is not None else current_cost.cost_type
        )
        recorded_at = (
            payload.recorded_at if payload.recorded_at is not None else current_cost.recorded_at
        )

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE costs
                SET name = ?, amount = ?, cost_type = ?, recorded_at = ?
                WHERE id = ?
                """,
                (name, str(amount), cost_type.value, recorded_at, cost_id),
            )
            affected_products = connection.execute(
                """
                SELECT product_id
                FROM product_variable_costs
                WHERE cost_id = ?
                """,
                (cost_id,),
            ).fetchall()
            connection.commit()

        if affected_products:
            from .product_repository import ProductRepository

            product_repository = ProductRepository(self.database)
            for row in affected_products:
                product_repository.refresh_product_prices(row["product_id"])

        return self.get_by_id(cost_id)

    def get_by_id(self, cost_id: int) -> Cost:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, amount, cost_type, recorded_at
                FROM costs
                WHERE id = ?
                """,
                (cost_id,),
            ).fetchone()

        if row is None:
            raise ValueError(f"Cost with id {cost_id} does not exist.")
        return self._map_row(row)

    def filter(self, filters: dict[str, object]) -> list[Cost]:
        query = """
            SELECT id, name, amount, cost_type, recorded_at
            FROM costs
            WHERE 1 = 1
        """
        params: list[object] = []

        if "name" in filters:
            query += " AND name LIKE ?"
            params.append(f"%{filters['name']}%")
        if "cost_type" in filters:
            query += " AND cost_type = ?"
            params.append(filters["cost_type"].value)
        if "min_amount" in filters:
            query += " AND CAST(amount AS REAL) >= ?"
            params.append(float(filters["min_amount"]))
        if "max_amount" in filters:
            query += " AND CAST(amount AS REAL) <= ?"
            params.append(float(filters["max_amount"]))
        if "recorded_at_from" in filters:
            query += " AND recorded_at >= ?"
            params.append(filters["recorded_at_from"])
        if "recorded_at_to" in filters:
            query += " AND recorded_at < ?"
            params.append(filters["recorded_at_to"])

        query += " ORDER BY recorded_at DESC, cost_type ASC, name COLLATE NOCASE ASC"

        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._map_row(row) for row in rows]

    def delete(self, cost_id: int) -> None:
        with self.database.connect() as connection:
            affected_products = connection.execute(
                """
                SELECT product_id
                FROM product_variable_costs
                WHERE cost_id = ?
                """,
                (cost_id,),
            ).fetchall()
            connection.execute(
                "DELETE FROM product_variable_costs WHERE cost_id = ?",
                (cost_id,),
            )
            cursor = connection.execute(
                "DELETE FROM costs WHERE id = ?",
                (cost_id,),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise ValueError(f"Cost with id {cost_id} does not exist.")

        if affected_products:
            from .product_repository import ProductRepository

            product_repository = ProductRepository(self.database)
            for row in affected_products:
                product_repository.refresh_product_prices(row["product_id"])

    def get_total_fixed_costs(self) -> Decimal:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(CAST(amount AS REAL)), 0) AS total_fixed_costs
                FROM costs
                WHERE cost_type = 'fixed'
                """
            ).fetchone()
        return Decimal(str(row["total_fixed_costs"])).quantize(Decimal("0.01"))

    @staticmethod
    def _map_row(row: object) -> Cost:
        return Cost(
            id=row["id"],
            name=row["name"],
            amount=Decimal(row["amount"]),
            cost_type=CostType(row["cost_type"]),
            recorded_at=row["recorded_at"],
        )
