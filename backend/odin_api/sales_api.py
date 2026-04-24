from __future__ import annotations

from .shared import ApiServices, Request, json_response, optional_number, serialize


def handle(request: Request, services: ApiServices):
    if request.parts[:2] != ["api", "sales"]:
        return None

    if request.parts == ["api", "sales"]:
        if request.method == "GET":
            sales = services.sales_service.filter_sales(
                product_id=int(request.query["product_id"][0]) if "product_id" in request.query else None,
                product_name=request.query.get("product_name", [None])[0],
                sale_date=request.query.get("sale_date", [None])[0],
                min_sale_price=optional_number(request.query.get("min_sale_price", [None])[0]),
                max_sale_price=optional_number(request.query.get("max_sale_price", [None])[0]),
            )
            return json_response(200, serialize(sales))
        if request.method == "POST":
            sale = services.sales_service.create_sale(
                int(request.body.get("product_id")),
                sale_price=optional_number(request.body.get("sale_price")),
                sale_date=request.body.get("sale_date"),
            )
            return json_response(201, serialize(sale))

    if len(request.parts) == 3:
        sale_id = int(request.parts[2])
        if request.method == "GET":
            return json_response(200, serialize(services.sales_service.get_sale(sale_id)))
        if request.method == "PATCH":
            sale = services.sales_service.update_sale(
                sale_id,
                sale_price=optional_number(request.body.get("sale_price")),
                sale_date=request.body.get("sale_date"),
            )
            return json_response(200, serialize(sale))
        if request.method == "DELETE":
            services.sales_service.delete_sale(sale_id)
            return json_response(200, {"deleted": True})

    return None
