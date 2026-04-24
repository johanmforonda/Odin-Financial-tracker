from __future__ import annotations

from .shared import ApiServices, Request, first, json_response, serialize


def handle(request: Request, services: ApiServices):
    if request.parts[:2] != ["api", "pricing"]:
        return None

    if request.parts == ["api", "pricing", "margin"] and request.method == "GET":
        minimum_revenue = first(request.query, "minimum_revenue")
        margin = services.pricing_service.calculate_margin(minimum_revenue)
        return json_response(200, {"minimum_revenue": float(minimum_revenue), "margin": float(margin)})

    if request.parts == ["api", "pricing", "recommendations"] and request.method == "POST":
        minimum_revenue = request.body.get("minimum_revenue")
        products = services.pricing_service.recommend_prices(minimum_revenue)
        return json_response(200, serialize(products))

    if len(request.parts) == 5 and request.parts[2] == "products" and request.parts[4] == "recommendation":
        product_id = int(request.parts[3])
        if request.method == "POST":
            product = services.pricing_service.recommend_price(
                product_id,
                request.body.get("minimum_revenue"),
            )
            return json_response(200, serialize(product))

    return None
