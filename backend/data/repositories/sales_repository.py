from __future__ import annotations

from decimal import Decimal

from backend.core.models.sale import Sale, SaleCreate, SaleUpdate

from ..database import DatabaseManager


class SalesRepository:
    """Persistence layer for sales records."""

    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def create(self, payload: SaleCreate, variable_cost_snapshots: list[dict[str, object]]) -> Sale:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO sales (product_id, product_name, sale_price, sale_date)
                VALUES (?, ?, ?, ?)
                """,
                (
                    payload.product_id,
                    payload.product_name,
                    str(payload.sale_price),
                    payload.sale_date,
                ),
            )
            sale_id = cursor.lastrowid
            for snapshot in variable_cost_snapshots:
                connection.execute(
                    """
                    INSERT INTO sale_variable_costs (
                        sale_id,
                        cost_id,
                        cost_name,
                        amount,
                        sale_date
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        sale_id,
                        snapshot["cost_id"],
                        snapshot["cost_name"],
                        str(snapshot["amount"]),
                        snapshot["sale_date"],
                    ),
                )
            connection.commit()
            return self.get_by_id(sale_id)

    def update(self, sale_id: int, payload: SaleUpdate) -> Sale:
        current_sale = self.get_by_id(sale_id)
        sale_price = payload.sale_price if payload.sale_price is not None else current_sale.sale_price
        sale_date = payload.sale_date if payload.sale_date is not None else current_sale.sale_date

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE sales
                SET sale_price = ?, sale_date = ?
                WHERE id = ?
                """,
                (str(sale_price), sale_date, sale_id),
            )
            connection.execute(
                """
                UPDATE sale_variable_costs
                SET sale_date = ?
                WHERE sale_id = ?
                """,
                (sale_date, sale_id),
            )
            connection.commit()
        return self.get_by_id(sale_id)

    def get_by_id(self, sale_id: int) -> Sale:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, product_id, product_name, sale_price, sale_date
                FROM sales
                WHERE id = ?
                """,
                (sale_id,),
            ).fetchone()

        if row is None:
            raise ValueError(f"Sale with id {sale_id} does not exist.")
        return self._map_row(row)

    def filter(self, filters: dict[str, object]) -> list[Sale]:
        query = """
            SELECT id, product_id, product_name, sale_price, sale_date
            FROM sales
            WHERE 1 = 1
        """
        params: list[object] = []

        if "product_id" in filters:
            query += " AND product_id = ?"
            params.append(filters["product_id"])
        if "product_name" in filters:
            query += " AND product_name LIKE ?"
            params.append(f"%{filters['product_name']}%")
        if "sale_date" in filters:
            query += " AND sale_date LIKE ?"
            params.append(f"{filters['sale_date']}%")
        if "min_sale_price" in filters:
            query += " AND CAST(sale_price AS REAL) >= ?"
            params.append(float(filters["min_sale_price"]))
        if "max_sale_price" in filters:
            query += " AND CAST(sale_price AS REAL) <= ?"
            params.append(float(filters["max_sale_price"]))

        query += " ORDER BY sale_date DESC, id DESC"

        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._map_row(row) for row in rows]

    def delete(self, sale_id: int) -> None:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM sales WHERE id = ?",
                (sale_id,),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise ValueError(f"Sale with id {sale_id} does not exist.")

    @staticmethod
    def _map_row(row: object) -> Sale:
        return Sale(
            id=row["id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            sale_price=Decimal(row["sale_price"]),
            sale_date=row["sale_date"],
        )
