from __future__ import annotations

from .shared import ApiServices, Request, json_response, optional_number, serialize


def handle(request: Request, services: ApiServices):
    if request.parts[:2] != ["api", "products"]:
        return None

    if request.parts == ["api", "products"]:
        if request.method == "GET":
            products = services.product_service.filter_products(
                name=request.query.get("name", [None])[0],
                min_cost_price=optional_number(request.query.get("min_cost_price", [None])[0]),
                max_cost_price=optional_number(request.query.get("max_cost_price", [None])[0]),
                min_recommended_price=optional_number(
                    request.query.get("min_recommended_price", [None])[0]
                ),
                max_recommended_price=optional_number(
                    request.query.get("max_recommended_price", [None])[0]
                ),
                min_sale_price=optional_number(request.query.get("min_sale_price", [None])[0]),
                max_sale_price=optional_number(request.query.get("max_sale_price", [None])[0]),
            )
            return json_response(200, serialize(products))
        if request.method == "POST":
            product = services.product_service.create_product(
                name=str(request.body.get("name", "")),
                sale_price=optional_number(request.body.get("sale_price")),
            )
            variable_cost_ids = request.body.get("variable_cost_ids", [])
            for cost_id in variable_cost_ids:
                services.product_service.add_variable_cost(product.id, int(cost_id))
            return json_response(201, _product_detail(product.id, services))

    if len(request.parts) == 3:
        product_id = int(request.parts[2])
        if request.method == "GET":
            return json_response(200, _product_detail(product_id, services))
        if request.method == "PATCH":
            product = services.product_service.update_product(
                product_id,
                name=request.body.get("name"),
                sale_price=optional_number(request.body.get("sale_price")),
            )
            if "variable_cost_ids" in request.body:
                _sync_variable_costs(product_id, request.body["variable_cost_ids"], services)
            return json_response(200, _product_detail(product.id, services))
        if request.method == "DELETE":
            services.product_service.delete_product(product_id)
            return json_response(200, {"deleted": True})

    if len(request.parts) == 4 and request.parts[3] == "costs":
        product_id = int(request.parts[2])
        if request.method == "GET":
            costs = services.product_service.list_variable_costs(product_id)
            return json_response(200, serialize(costs))
        if request.method == "POST":
            cost_id = int(request.body.get("cost_id"))
            product = services.product_service.add_variable_cost(product_id, cost_id)
            return json_response(200, _product_detail(product.id, services))

    if len(request.parts) == 5 and request.parts[3] == "costs":
        product_id = int(request.parts[2])
        cost_id = int(request.parts[4])
        if request.method == "DELETE":
            product = services.product_service.remove_variable_cost(product_id, cost_id)
            return json_response(200, _product_detail(product.id, services))

    return None


def _product_detail(product_id: int, services: ApiServices) -> dict[str, object]:
    product = services.product_service.get_product(product_id)
    variable_costs = services.product_service.list_variable_costs(product_id)
    return {
        **serialize(product),
        "variable_costs": serialize(variable_costs),
    }


def _sync_variable_costs(product_id: int, requested_cost_ids: list[object], services: ApiServices) -> None:
    current_cost_ids = {cost.id for cost in services.product_service.list_variable_costs(product_id)}
    desired_cost_ids = {int(cost_id) for cost_id in requested_cost_ids}
    for cost_id in current_cost_ids - desired_cost_ids:
        services.product_service.remove_variable_cost(product_id, cost_id)
    for cost_id in desired_cost_ids - current_cost_ids:
        services.product_service.add_variable_cost(product_id, cost_id)
