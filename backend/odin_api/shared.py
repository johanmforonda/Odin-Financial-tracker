from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, urlparse

from backend.app.bootstrap import build_services
from backend.core.stats import StatsService
from backend.core.services.cost_service import CostService
from backend.core.services.pricing_service import PricingService
from backend.core.services.product_service import ProductService
from backend.core.services.sales_service import SalesService


@dataclass(slots=True)
class ApiServices:
    product_service: ProductService
    cost_service: CostService
    pricing_service: PricingService
    sales_service: SalesService
    stats_service: StatsService


@dataclass(slots=True)
class Request:
    method: str
    path: str
    parts: list[str]
    query: dict[str, list[str]]
    body: dict[str, Any]


@dataclass(slots=True)
class Response:
    status: int
    payload: Any


def create_services() -> ApiServices:
    (
        product_service,
        cost_service,
        pricing_service,
        sales_service,
        stats_service,
    ) = build_services()
    return ApiServices(
        product_service=product_service,
        cost_service=cost_service,
        pricing_service=pricing_service,
        sales_service=sales_service,
        stats_service=stats_service,
    )


def parse_request(method: str, path: str, body: bytes | None = None) -> Request:
    parsed = urlparse(path)
    content = body.decode("utf-8") if body else ""
    json_body = json.loads(content) if content else {}
    clean_path = parsed.path.rstrip("/") or "/"
    parts = [part for part in clean_path.split("/") if part]
    return Request(
        method=method,
        path=clean_path,
        parts=parts,
        query=parse_qs(parsed.query),
        body=json_body,
    )


def json_response(status: int, payload: Any) -> Response:
    return Response(status=status, payload=payload)


def serialize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if is_dataclass(value):
        return {key: serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    return value


def first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def optional_number(value: Any) -> Any | None:
    if value in (None, ""):
        return None
    return value
