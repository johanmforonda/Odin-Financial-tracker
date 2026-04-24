from __future__ import annotations

from .shared import ApiServices, Request, json_response, optional_number, serialize


def handle(request: Request, services: ApiServices):
    if request.parts[:2] != ["api", "costs"]:
        return None

    if request.parts == ["api", "costs"]:
        if request.method == "GET":
            costs = services.cost_service.filter_costs(
                name=request.query.get("name", [None])[0],
                cost_type=request.query.get("cost_type", [None])[0],
                min_amount=optional_number(request.query.get("min_amount", [None])[0]),
                max_amount=optional_number(request.query.get("max_amount", [None])[0]),
            )
            return json_response(200, serialize(costs))
        if request.method == "POST":
            cost = services.cost_service.create_cost(
                name=str(request.body.get("name", "")),
                amount=request.body.get("amount"),
                cost_type=str(request.body.get("cost_type", "")),
            )
            return json_response(201, serialize(cost))

    if len(request.parts) == 3:
        cost_id = int(request.parts[2])
        if request.method == "GET":
            return json_response(200, serialize(services.cost_service.get_cost(cost_id)))
        if request.method == "PATCH":
            cost = services.cost_service.update_cost(
                cost_id,
                name=request.body.get("name"),
                amount=optional_number(request.body.get("amount")),
                cost_type=request.body.get("cost_type"),
            )
            return json_response(200, serialize(cost))
        if request.method == "DELETE":
            services.cost_service.delete_cost(cost_id)
            return json_response(200, {"deleted": True})

    return None
