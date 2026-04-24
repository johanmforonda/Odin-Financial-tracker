from __future__ import annotations

from .shared import ApiServices, Request, first, json_response, serialize


def handle(request: Request, services: ApiServices):
    if request.parts[:2] != ["api", "stats"]:
        return None

    if request.parts == ["api", "stats", "monthly"] and request.method == "GET":
        month = first(request.query, "month")
        stats = services.stats_service.get_monthly_stats(month)
        return json_response(200, serialize(stats))

    if request.parts == ["api", "stats", "series"] and request.method == "GET":
        month = first(request.query, "month")
        periods = first(request.query, "periods")
        stats = services.stats_service.get_profitability_series(
            month=month,
            periods=int(periods) if periods is not None else 6,
        )
        return json_response(200, serialize(stats))

    return None
