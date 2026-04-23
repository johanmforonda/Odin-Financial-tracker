from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from data.database import DatabaseManager
from main import build_services


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"


def serialize(value):
    if isinstance(value, Decimal):
        return float(value)
    if is_dataclass(value):
        return {key: serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    return value


def optional_value(value: object) -> object | None:
    if value in (None, ""):
        return None
    return value


class OdinWebBackend:
    def __init__(self) -> None:
        (
            self.product_service,
            self.cost_service,
            self.pricing_service,
            self.sales_service,
            self.stats_service,
        ) = build_services()
        self.database = DatabaseManager()
        self.database.initialize()

    def dashboard(self, month: str | None = None) -> dict[str, object]:
        resolved_month = month or datetime.now(UTC).strftime("%Y-%m")
        products = []
        for product in self.product_service.filter_products():
            variable_costs = self.product_service.list_variable_costs(product.id)
            products.append(
                {
                    **serialize(product),
                    "variable_costs": serialize(variable_costs),
                    "margin_per_sale": float(product.sale_price - product.cost_price),
                }
            )

        fixed_costs = serialize(self.cost_service.filter_costs(cost_type="fixed"))
        variable_costs = serialize(self.cost_service.filter_costs(cost_type="variable"))
        monthly_stats = serialize(self.stats_service.get_monthly_stats_as_dict(resolved_month))
        profitability_series = serialize(
            self.stats_service.get_profitability_series(resolved_month, periods=6)
        )

        return {
            "month": resolved_month,
            "products": products,
            "fixed_costs": fixed_costs,
            "variable_costs": variable_costs,
            "stats": {
                **monthly_stats,
                "profitability_series": profitability_series,
                "fixed_breakdown": self._cost_breakdown("fixed", resolved_month),
                "variable_breakdown": self._variable_breakdown(resolved_month),
                "daily_sales": self._daily_sales(resolved_month),
                "top_products": self._top_products(resolved_month),
                "today_sales": self._today_sales(),
            },
        }

    def create_product(self, payload: dict[str, object]) -> dict[str, object]:
        product = self.product_service.create_product(
            name=str(payload.get("name", "")),
            sale_price=optional_value(payload.get("sale_price")),
        )
        for cost_id in payload.get("variable_cost_ids", []):
            self.product_service.add_variable_cost(product.id, int(cost_id))
        return self._product_detail(product.id)

    def update_product(self, product_id: int, payload: dict[str, object]) -> dict[str, object]:
        product = self.product_service.update_product(
            product_id,
            name=payload.get("name"),
            sale_price=optional_value(payload.get("sale_price")),
        )
        if "variable_cost_ids" in payload:
            current_cost_ids = {
                cost.id for cost in self.product_service.list_variable_costs(product_id)
            }
            requested_cost_ids = {int(cost_id) for cost_id in payload["variable_cost_ids"]}
            for cost_id in current_cost_ids - requested_cost_ids:
                self.product_service.remove_variable_cost(product_id, cost_id)
            for cost_id in requested_cost_ids - current_cost_ids:
                self.product_service.add_variable_cost(product_id, cost_id)
        return self._product_detail(product.id)

    def delete_product(self, product_id: int) -> dict[str, object]:
        self.product_service.delete_product(product_id)
        return {"deleted": True}

    def create_cost(self, payload: dict[str, object]) -> dict[str, object]:
        cost = self.cost_service.create_cost(
            name=str(payload.get("name", "")),
            amount=payload.get("amount"),
            cost_type=str(payload.get("cost_type", "")),
        )
        return serialize(cost)

    def update_cost(self, cost_id: int, payload: dict[str, object]) -> dict[str, object]:
        cost = self.cost_service.update_cost(
            cost_id,
            name=payload.get("name"),
            amount=optional_value(payload.get("amount")),
            cost_type=payload.get("cost_type"),
        )
        return serialize(cost)

    def delete_cost(self, cost_id: int) -> dict[str, object]:
        self.cost_service.delete_cost(cost_id)
        return {"deleted": True}

    def create_sale(self, product_id: int) -> dict[str, object]:
        sale = self.sales_service.create_sale(product_id)
        return serialize(sale)

    def _product_detail(self, product_id: int) -> dict[str, object]:
        product = self.product_service.get_product(product_id)
        variable_costs = self.product_service.list_variable_costs(product_id)
        return {
            **serialize(product),
            "variable_costs": serialize(variable_costs),
            "margin_per_sale": float(product.sale_price - product.cost_price),
        }

    def _today_sales(self) -> dict[str, object]:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        sales = self.sales_service.filter_sales(sale_date=today)
        revenue = sum((sale.sale_price for sale in sales), start=Decimal("0.00"))
        return {
            "count": len(sales),
            "revenue": float(revenue),
        }

    def _cost_breakdown(self, cost_type: str, month: str) -> list[dict[str, object]]:
        start_date, end_date = self._month_range(month)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT name, CAST(amount AS REAL) AS total
                FROM costs
                WHERE cost_type = ?
                  AND recorded_at >= ?
                  AND recorded_at < ?
                ORDER BY total DESC, name COLLATE NOCASE ASC
                """,
                (cost_type, start_date, end_date),
            ).fetchall()
        total = sum((Decimal(str(row["total"])) for row in rows), start=Decimal("0.00"))
        return [
            {
                "name": row["name"],
                "value": float(Decimal(str(row["total"]))),
                "percentage": float(
                    (Decimal(str(row["total"])) / total * Decimal("100")).quantize(Decimal("0.01"))
                )
                if total
                else 0.0,
            }
            for row in rows
        ]

    def _variable_breakdown(self, month: str) -> list[dict[str, object]]:
        start_date, end_date = self._month_range(month)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT cost_name AS name, COALESCE(SUM(CAST(amount AS REAL)), 0) AS total
                FROM sale_variable_costs
                WHERE sale_date >= ?
                  AND sale_date < ?
                GROUP BY cost_name
                ORDER BY total DESC, cost_name COLLATE NOCASE ASC
                """,
                (start_date, end_date),
            ).fetchall()
        total = sum((Decimal(str(row["total"])) for row in rows), start=Decimal("0.00"))
        return [
            {
                "name": row["name"],
                "value": float(Decimal(str(row["total"]))),
                "percentage": float(
                    (Decimal(str(row["total"])) / total * Decimal("100")).quantize(Decimal("0.01"))
                )
                if total
                else 0.0,
            }
            for row in rows
        ]

    def _daily_sales(self, month: str) -> list[dict[str, object]]:
        start_date, end_date = self._month_range(month)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT substr(sale_date, 1, 10) AS day, COUNT(*) AS sales_count,
                       COALESCE(SUM(CAST(sale_price AS REAL)), 0) AS revenue
                FROM sales
                WHERE sale_date >= ?
                  AND sale_date < ?
                GROUP BY substr(sale_date, 1, 10)
                ORDER BY day ASC
                """,
                (start_date, end_date),
            ).fetchall()
        return [
            {
                "day": row["day"],
                "sales_count": row["sales_count"],
                "revenue": float(Decimal(str(row["revenue"]))),
            }
            for row in rows
        ]

    def _top_products(self, month: str) -> list[dict[str, object]]:
        start_date, end_date = self._month_range(month)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT s.product_id,
                       s.product_name AS name,
                       COUNT(*) AS sales_count,
                       COALESCE(SUM(CAST(s.sale_price AS REAL)), 0) AS revenue,
                       COALESCE(SUM(CAST(s.sale_price AS REAL)), 0) - COALESCE(SUM(costs.total_cost), 0) AS margin
                FROM sales s
                LEFT JOIN (
                    SELECT sale_id, COALESCE(SUM(CAST(amount AS REAL)), 0) AS total_cost
                    FROM sale_variable_costs
                    GROUP BY sale_id
                ) costs ON costs.sale_id = s.id
                WHERE s.sale_date >= ?
                  AND s.sale_date < ?
                GROUP BY s.product_id, s.product_name
                ORDER BY revenue DESC, sales_count DESC, s.product_name COLLATE NOCASE ASC
                LIMIT 6
                """,
                (start_date, end_date),
            ).fetchall()
        return [
            {
                "product_id": row["product_id"],
                "name": row["name"],
                "sales_count": row["sales_count"],
                "revenue": float(Decimal(str(row["revenue"]))),
                "margin": float(Decimal(str(row["margin"]))),
            }
            for row in rows
        ]

    @staticmethod
    def _month_range(month: str) -> tuple[str, str]:
        start_date = datetime.strptime(month, "%Y-%m")
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
        return (
            start_date.isoformat(timespec="seconds"),
            end_date.isoformat(timespec="seconds"),
        )


backend = OdinWebBackend()


class OdinRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/dashboard":
            query = parse_qs(parsed.query)
            month = query.get("month", [None])[0]
            return self._send_json(backend.dashboard(month))
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_json_body()
        try:
            if parsed.path == "/api/products":
                return self._send_json(backend.create_product(payload), HTTPStatus.CREATED)
            if parsed.path == "/api/costs":
                return self._send_json(backend.create_cost(payload), HTTPStatus.CREATED)
            if parsed.path.startswith("/api/products/") and parsed.path.endswith("/sell"):
                product_id = int(parsed.path.split("/")[3])
                return self._send_json(backend.create_sale(product_id), HTTPStatus.CREATED)
        except ValueError as error:
            return self._send_error(str(error), HTTPStatus.BAD_REQUEST)
        return self._send_error("Route not found.", HTTPStatus.NOT_FOUND)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_json_body()
        try:
            if parsed.path.startswith("/api/products/"):
                product_id = int(parsed.path.split("/")[3])
                return self._send_json(backend.update_product(product_id, payload))
            if parsed.path.startswith("/api/costs/"):
                cost_id = int(parsed.path.split("/")[3])
                return self._send_json(backend.update_cost(cost_id, payload))
        except ValueError as error:
            return self._send_error(str(error), HTTPStatus.BAD_REQUEST)
        return self._send_error("Route not found.", HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path.startswith("/api/products/"):
                product_id = int(parsed.path.split("/")[3])
                return self._send_json(backend.delete_product(product_id))
            if parsed.path.startswith("/api/costs/"):
                cost_id = int(parsed.path.split("/")[3])
                return self._send_json(backend.delete_cost(cost_id))
        except ValueError as error:
            return self._send_error(str(error), HTTPStatus.BAD_REQUEST)
        return self._send_error("Route not found.", HTTPStatus.NOT_FOUND)

    def _read_json_body(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return {}
        raw_body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw_body) if raw_body else {}

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message: str, status: HTTPStatus) -> None:
        self._send_json({"error": message}, status)

    def log_message(self, format: str, *args) -> None:
        return


def run() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), OdinRequestHandler)
    print("Odin web running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
