from __future__ import annotations

from decimal import Decimal

from backend.core.models.cost import Cost, CostType
from backend.core.domain.money import to_money
from backend.core.models.product import Product, ProductCreate, ProductUpdate

from backend.data.database import DatabaseManager


class ProductRepository:
    """Persistence layer for products."""

    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def create(self, payload: ProductCreate) -> Product:
        sale_price = payload.sale_price if payload.sale_price is not None else Decimal("0.00")
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO products (name, cost_price, recommended_price, sale_price)
                VALUES (?, ?, ?, ?)
                """,
                (payload.name, "0.00", "0.00", str(sale_price)),
            )
            connection.commit()
            return self.get_by_id(cursor.lastrowid)

    def update(self, product_id: int, payload: ProductUpdate) -> Product:
        current_product = self.get_by_id(product_id)
        name = payload.name if payload.name is not None else current_product.name
        cost_price = self._calculate_cost_price(product_id)
        sale_price = payload.sale_price if payload.sale_price is not None else current_product.sale_price

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE products
                SET name = ?, cost_price = ?, sale_price = ?
                WHERE id = ?
                """,
                (name, str(cost_price), str(sale_price), product_id),
            )
            connection.commit()

        return self.get_by_id(product_id)

    def get_by_id(self, product_id: int) -> Product:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, cost_price, recommended_price, sale_price
                FROM products
                WHERE id = ?
                """,
                (product_id,),
            ).fetchone()

        if row is None:
            raise ValueError(f"Product with id {product_id} does not exist.")
        return self._map_product(row)

    def search_by_name(self, term: str) -> list[Product]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, cost_price, recommended_price, sale_price
                FROM products
                WHERE name LIKE ?
                ORDER BY name COLLATE NOCASE ASC
                """,
                (f"%{term}%",),
            ).fetchall()
        return [self._map_product(row) for row in rows]

    def filter(self, filters: dict[str, object]) -> list[Product]:
        query = """
            SELECT id, name, cost_price, recommended_price, sale_price
            FROM products
            WHERE 1 = 1
        """
        params: list[object] = []

        if "name" in filters:
            query += " AND name LIKE ?"
            params.append(f"%{filters['name']}%")
        if "min_cost_price" in filters:
            query += " AND CAST(cost_price AS REAL) >= ?"
            params.append(float(filters["min_cost_price"]))
        if "max_cost_price" in filters:
            query += " AND CAST(cost_price AS REAL) <= ?"
            params.append(float(filters["max_cost_price"]))
        if "min_recommended_price" in filters:
            query += " AND CAST(recommended_price AS REAL) >= ?"
            params.append(float(filters["min_recommended_price"]))
        if "max_recommended_price" in filters:
            query += " AND CAST(recommended_price AS REAL) <= ?"
            params.append(float(filters["max_recommended_price"]))
        if "min_sale_price" in filters:
            query += " AND CAST(sale_price AS REAL) >= ?"
            params.append(float(filters["min_sale_price"]))
        if "max_sale_price" in filters:
            query += " AND CAST(sale_price AS REAL) <= ?"
            params.append(float(filters["max_sale_price"]))

        query += " ORDER BY name COLLATE NOCASE ASC"

        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._map_product(row) for row in rows]

    def add_variable_cost(self, product_id: int, cost_id: int) -> None:
        self.get_by_id(product_id)
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO product_variable_costs (product_id, cost_id)
                VALUES (?, ?)
                """,
                (product_id, cost_id),
            )
            connection.commit()
        self.refresh_product_prices(product_id)

    def remove_variable_cost(self, product_id: int, cost_id: int) -> None:
        self.get_by_id(product_id)
        with self.database.connect() as connection:
            connection.execute(
                """
                DELETE FROM product_variable_costs
                WHERE product_id = ? AND cost_id = ?
                """,
                (product_id, cost_id),
            )
            connection.commit()
        self.refresh_product_prices(product_id)

    def list_variable_costs(self, product_id: int) -> list[Cost]:
        self.get_by_id(product_id)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.name, c.amount, c.cost_type, c.recorded_at
                FROM costs c
                INNER JOIN product_variable_costs pvc ON pvc.cost_id = c.id
                WHERE pvc.product_id = ?
                ORDER BY c.name COLLATE NOCASE ASC
                """,
                (product_id,),
            ).fetchall()
        return [self._map_cost(row) for row in rows]

    def delete(self, product_id: int) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM product_variable_costs WHERE product_id = ?",
                (product_id,),
            )
            cursor = connection.execute(
                "DELETE FROM products WHERE id = ?",
                (product_id,),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise ValueError(f"Product with id {product_id} does not exist.")

    def refresh_product_prices(self, product_id: int) -> None:
        product = self.get_by_id(product_id)
        cost_price = self._calculate_cost_price(product_id)
        sale_price = product.sale_price
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE products
                SET cost_price = ?, sale_price = ?
                WHERE id = ?
                """,
                (str(cost_price), str(sale_price), product_id),
            )
            connection.commit()

    def update_prices(
        self,
        *,
        product_id: int,
        cost_price: Decimal,
        recommended_price: Decimal,
        sale_price: Decimal,
    ) -> None:
        self.get_by_id(product_id)
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE products
                SET cost_price = ?, recommended_price = ?, sale_price = ?
                WHERE id = ?
                """,
                (str(cost_price), str(recommended_price), str(sale_price), product_id),
            )
            connection.commit()

    def _calculate_cost_price(self, product_id: int) -> Decimal:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(CAST(c.amount AS REAL)), 0)
                AS total_variable_cost
                FROM costs c
                INNER JOIN product_variable_costs pvc ON pvc.cost_id = c.id
                WHERE pvc.product_id = ? AND c.cost_type = 'variable'
                """,
                (product_id,),
            ).fetchone()
        return to_money(row["total_variable_cost"])

    @staticmethod
    def _map_product(row: object) -> Product:
        return Product(
            id=row["id"],
            name=row["name"],
            cost_price=Decimal(row["cost_price"]),
            recommended_price=Decimal(row["recommended_price"]),
            sale_price=Decimal(row["sale_price"]),
        )

    @staticmethod
    def _map_cost(row: object) -> Cost:
        return Cost(
            id=row["id"],
            name=row["name"],
            amount=Decimal(row["amount"]),
            cost_type=CostType(row["cost_type"]),
            recorded_at=row["recorded_at"],
        )
