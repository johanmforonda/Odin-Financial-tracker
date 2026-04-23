from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "odin.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


class DatabaseManager:
    """Handle SQLite connections and schema initialization."""

    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            self._migrate_products_table(connection)
            self._ensure_costs_have_recorded_at(connection)
            self._ensure_sale_variable_costs(connection)
            self._rebuild_product_foreign_keys(connection)
            connection.commit()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _migrate_products_table(connection: sqlite3.Connection) -> None:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(products)").fetchall()
        }
        legacy_columns = {"nombre", "precio_coste", "tarifa", "precio_venta"}
        previous_columns = {"name", "cost_price", "rate", "sale_price"}

        if legacy_columns.issubset(columns):
            connection.execute("ALTER TABLE products RENAME TO products_legacy")
            connection.executescript(
                """
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cost_price TEXT NOT NULL DEFAULT '0.00',
                    recommended_price TEXT NOT NULL DEFAULT '0.00',
                    sale_price TEXT NOT NULL DEFAULT '0.00'
                );

                INSERT INTO products (id, name, cost_price, recommended_price, sale_price)
                SELECT id, nombre, precio_coste, precio_venta, precio_venta
                FROM products_legacy;

                DROP TABLE products_legacy;
                """
            )
            return

        if previous_columns.issubset(columns) and "recommended_price" not in columns:
            connection.execute("ALTER TABLE products RENAME TO products_previous")
            connection.executescript(
                """
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cost_price TEXT NOT NULL DEFAULT '0.00',
                    recommended_price TEXT NOT NULL DEFAULT '0.00',
                    sale_price TEXT NOT NULL DEFAULT '0.00'
                );

                INSERT INTO products (id, name, cost_price, recommended_price, sale_price)
                SELECT id, name, cost_price, sale_price, sale_price
                FROM products_previous;

                DROP TABLE products_previous;
                """
            )

    @staticmethod
    def _ensure_costs_have_recorded_at(connection: sqlite3.Connection) -> None:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(costs)").fetchall()
        }
        if "recorded_at" not in columns:
            connection.execute("ALTER TABLE costs ADD COLUMN recorded_at TEXT")
        connection.execute(
            """
            UPDATE costs
            SET recorded_at = COALESCE(recorded_at, strftime('%Y-%m-%dT%H:%M:%S', 'now'))
            """
        )

    @staticmethod
    def _ensure_sale_variable_costs(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sale_variable_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                cost_id INTEGER NOT NULL,
                cost_name TEXT NOT NULL,
                amount TEXT NOT NULL,
                sale_date TEXT NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                FOREIGN KEY (cost_id) REFERENCES costs(id)
            );
            """
        )

    @staticmethod
    def _rebuild_product_foreign_keys(connection: sqlite3.Connection) -> None:
        product_cost_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(product_variable_costs)"
        ).fetchall()
        if any(row[2] != "products" for row in product_cost_foreign_keys):
            connection.execute("ALTER TABLE product_variable_costs RENAME TO product_variable_costs_legacy")
            connection.executescript(
                """
                CREATE TABLE product_variable_costs (
                    product_id INTEGER NOT NULL,
                    cost_id INTEGER NOT NULL,
                    PRIMARY KEY (product_id, cost_id),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    FOREIGN KEY (cost_id) REFERENCES costs(id) ON DELETE CASCADE
                );

                INSERT INTO product_variable_costs (product_id, cost_id)
                SELECT product_id, cost_id
                FROM product_variable_costs_legacy;

                DROP TABLE product_variable_costs_legacy;
                """
            )

        sales_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(sales)"
        ).fetchall()
        if any(row[2] != "products" for row in sales_foreign_keys):
            connection.execute("ALTER TABLE sales RENAME TO sales_legacy")
            connection.executescript(
                """
                CREATE TABLE sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    sale_price TEXT NOT NULL,
                    sale_date TEXT NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );

                INSERT INTO sales (id, product_id, product_name, sale_price, sale_date)
                SELECT id, product_id, product_name, sale_price, sale_date
                FROM sales_legacy;

                DROP TABLE sales_legacy;
                """
            )

        sale_variable_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(sale_variable_costs)"
        ).fetchall()
        if any(row[2] not in {"sales", "costs"} for row in sale_variable_foreign_keys):
            connection.execute("ALTER TABLE sale_variable_costs RENAME TO sale_variable_costs_legacy")
            connection.executescript(
                """
                CREATE TABLE sale_variable_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    cost_id INTEGER NOT NULL,
                    cost_name TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    sale_date TEXT NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY (cost_id) REFERENCES costs(id)
                );

                INSERT INTO sale_variable_costs (id, sale_id, cost_id, cost_name, amount, sale_date)
                SELECT id, sale_id, cost_id, cost_name, amount, sale_date
                FROM sale_variable_costs_legacy;

                DROP TABLE sale_variable_costs_legacy;
                """
            )
