from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.bootstrap import build_services
from core.models.cost import Cost
from core.models.product import Product
from core.models.sale import Sale
from core.stats import StatsService
from core.services.cost_service import CostService
from core.services.pricing_service import PricingService
from core.services.product_service import ProductService
from core.services.sales_service import SalesService

from . import ui

class OdinCLIApp:
    def __init__(self) -> None:
        (
            self.product_service,
            self.cost_service,
            self.pricing_service,
            self.sales_service,
            self.stats_service,
        ) = build_services()

    def run(self) -> None:
        while True:
            self._render_home()
            option = self._ask("Selecciona una opcion").lower()
            if option == "1":
                self._products_menu()
            elif option == "2":
                self._costs_menu()
            elif option == "3":
                self._pricing_menu()
            elif option == "4":
                self._sales_menu()
            elif option == "5":
                self._stats_menu()
            elif option == "0":
                ui.clear_screen()
                print(ui.title("ODIN CLI", "Hasta luego."))
                return
            else:
                self._pause(ui.error("Opcion no valida."))

    def _render_home(self) -> None:
        ui.clear_screen()
        print(ui.title("ODIN CLI", "Gestiona productos, costes, precios y ventas desde terminal."))
        print(self._dashboard_snapshot())
        print(
            ui.menu(
                "Menu principal",
                [
                    ("1", "Productos"),
                    ("2", "Costes"),
                    ("3", "Precios y recomendaciones"),
                    ("4", "Ventas"),
                    ("5", "Estadisticas"),
                    ("0", "Salir"),
                ],
            )
        )

    def _dashboard_snapshot(self) -> str:
        month = self.stats_service.get_monthly_stats()
        products = self.product_service.filter_products()
        costs = self.cost_service.filter_costs()
        sales = self.sales_service.filter_sales()
        return ui.panel(
            "Resumen",
            [
                ui.key_value(
                    [
                        ("Mes", month.month),
                        ("Productos", len(products)),
                        ("Costes", len(costs)),
                        ("Ventas", len(sales)),
                        ("Ingresos", month.total_income),
                        ("Margen", month.total_margin),
                        ("Rentabilidad", f"{month.profitability:.2f}%"),
                    ]
                )
            ],
        )

    def _products_menu(self) -> None:
        while True:
            self._render_products()
            option = self._ask("Elige una accion").lower()
            try:
                if option == "1":
                    self._create_product()
                elif option == "2":
                    self._update_product()
                elif option == "3":
                    self._delete_product()
                elif option == "4":
                    self._manage_product_costs()
                elif option == "5":
                    self._search_products()
                elif option == "b":
                    return
                else:
                    self._pause(ui.error("Opcion no valida."))
            except ValueError as error:
                self._pause(ui.error(str(error)))

    def _render_products(self) -> None:
        ui.clear_screen()
        products = self.product_service.filter_products()
        print(ui.title("ODIN CLI", "Modulo de productos"))
        print(
            ui.panel(
                "Productos",
                [
                    ui.table(
                        ["ID", "Nombre", "Coste", "Recomendado", "Venta"],
                        [
                            [
                                product.id,
                                product.name,
                                product.cost_price,
                                product.recommended_price,
                                product.sale_price,
                            ]
                            for product in products
                        ],
                    )
                ],
            )
        )
        print(
            ui.menu(
                "Acciones",
                [
                    ("1", "Crear producto"),
                    ("2", "Editar producto"),
                    ("3", "Eliminar producto"),
                    ("4", "Asignar o quitar costes variables"),
                    ("5", "Buscar o filtrar productos"),
                    ("b", "Volver"),
                ],
            )
        )

    def _create_product(self) -> None:
        name = self._ask_required("Nombre del producto")
        sale_price = self._ask_optional_decimal("Precio de venta inicial (opcional)")
        product = self.product_service.create_product(name=name, sale_price=sale_price)
        self._pause(ui.success(f"Producto creado con ID {product.id}."))

    def _update_product(self) -> None:
        product = self._select_product()
        print(ui.panel("Producto actual", [self._product_detail(product)]))
        name = self._ask_optional_text("Nuevo nombre (enter para mantener)")
        sale_price = self._ask_optional_decimal("Nuevo precio de venta (enter para mantener)")
        updated = self.product_service.update_product(
            product.id,
            name=name if name != "" else None,
            sale_price=sale_price,
        )
        self._pause(ui.success(f"Producto {updated.id} actualizado."))

    def _delete_product(self) -> None:
        product = self._select_product()
        confirmed = self._ask(f"Escribe SI para eliminar '{product.name}'")
        if confirmed != "SI":
            self._pause(ui.info("Operacion cancelada."))
            return
        self.product_service.delete_product(product.id)
        self._pause(ui.success("Producto eliminado."))

    def _manage_product_costs(self) -> None:
        product = self._select_product()
        while True:
            ui.clear_screen()
            variable_costs = self.product_service.list_variable_costs(product.id)
            available_costs = self.cost_service.filter_costs(cost_type="variable")
            print(ui.title("ODIN CLI", f"Costes variables de {product.name}"))
            print(
                ui.panel(
                    "Asignados",
                    [
                        ui.table(
                            ["ID", "Nombre", "Importe"],
                            [[cost.id, cost.name, cost.amount] for cost in variable_costs],
                        )
                    ],
                )
            )
            print(
                ui.panel(
                    "Disponibles",
                    [
                        ui.table(
                            ["ID", "Nombre", "Importe"],
                            [[cost.id, cost.name, cost.amount] for cost in available_costs],
                        )
                    ],
                )
            )
            print(
                ui.menu(
                    "Acciones",
                    [
                        ("1", "Asignar coste variable"),
                        ("2", "Quitar coste variable"),
                        ("b", "Volver"),
                    ],
                )
            )
            option = self._ask("Elige una accion").lower()
            if option == "1":
                cost_id = self._ask_int("ID del coste variable")
                self.product_service.add_variable_cost(product.id, cost_id)
                product = self.product_service.get_product(product.id)
                self._pause(ui.success("Coste asignado."))
            elif option == "2":
                cost_id = self._ask_int("ID del coste a quitar")
                self.product_service.remove_variable_cost(product.id, cost_id)
                product = self.product_service.get_product(product.id)
                self._pause(ui.success("Coste retirado."))
            elif option == "b":
                return
            else:
                self._pause(ui.error("Opcion no valida."))

    def _search_products(self) -> None:
        term = self._ask_optional_text("Texto a buscar")
        min_sale_price = self._ask_optional_decimal("Precio minimo de venta (opcional)", allow_zero=True)
        max_sale_price = self._ask_optional_decimal("Precio maximo de venta (opcional)", allow_zero=True)
        min_recommended = self._ask_optional_decimal("Precio recomendado minimo (opcional)", allow_zero=True)
        max_recommended = self._ask_optional_decimal("Precio recomendado maximo (opcional)", allow_zero=True)

        if term and not any([min_sale_price, max_sale_price, min_recommended, max_recommended]):
            results = self.product_service.search_products(term)
        else:
            results = self.product_service.filter_products(
                name=term or None,
                min_sale_price=min_sale_price,
                max_sale_price=max_sale_price,
                min_recommended_price=min_recommended,
                max_recommended_price=max_recommended,
            )

        self._pause(
            ui.panel(
                "Resultados",
                [
                    ui.table(
                        ["ID", "Nombre", "Coste", "Recomendado", "Venta"],
                        [
                            [
                                product.id,
                                product.name,
                                product.cost_price,
                                product.recommended_price,
                                product.sale_price,
                            ]
                            for product in results
                        ],
                    )
                ],
            )
        )

    def _pricing_menu(self) -> None:
        while True:
            ui.clear_screen()
            products = self.product_service.filter_products()
            print(ui.title("ODIN CLI", "Modulo de precios"))
            print(
                ui.panel(
                    "Productos",
                    [
                        ui.table(
                            ["ID", "Nombre", "Coste", "Recomendado", "Venta"],
                            [
                                [
                                    product.id,
                                    product.name,
                                    product.cost_price,
                                    product.recommended_price,
                                    product.sale_price,
                                ]
                                for product in products
                            ],
                        )
                    ],
                )
            )
            print(
                ui.menu(
                    "Acciones",
                    [
                        ("1", "Recomendar precio de un producto"),
                        ("2", "Recalcular todos los productos"),
                        ("3", "Calcular margen objetivo"),
                        ("b", "Volver"),
                    ],
                )
            )
            option = self._ask("Elige una accion").lower()
            try:
                if option == "1":
                    product = self._select_product()
                    minimum_revenue = self._ask_decimal("Ingresos minimos del mes")
                    updated = self.pricing_service.recommend_price(product.id, minimum_revenue)
                    self._pause(ui.panel("Precio recomendado", [self._product_detail(updated)]))
                elif option == "2":
                    minimum_revenue = self._ask_decimal("Ingresos minimos del mes")
                    updated_products = self.pricing_service.recommend_prices(minimum_revenue)
                    self._pause(
                        ui.panel(
                            "Recomendaciones actualizadas",
                            [
                                ui.table(
                                    ["ID", "Nombre", "Coste", "Recomendado", "Venta"],
                                    [
                                        [
                                            product.id,
                                            product.name,
                                            product.cost_price,
                                            product.recommended_price,
                                            product.sale_price,
                                        ]
                                        for product in updated_products
                                    ],
                                )
                            ],
                        )
                    )
                elif option == "3":
                    minimum_revenue = self._ask_decimal("Ingresos minimos del mes")
                    margin = self.pricing_service.calculate_margin(minimum_revenue)
                    self._pause(ui.success(f"Margen objetivo calculado: {margin:.4f}"))
                elif option == "b":
                    return
                else:
                    self._pause(ui.error("Opcion no valida."))
            except ValueError as error:
                self._pause(ui.error(str(error)))

    def _costs_menu(self) -> None:
        while True:
            self._render_costs()
            option = self._ask("Elige una accion").lower()
            try:
                if option == "1":
                    self._create_cost()
                elif option == "2":
                    self._update_cost()
                elif option == "3":
                    self._delete_cost()
                elif option == "4":
                    self._filter_costs()
                elif option == "b":
                    return
                else:
                    self._pause(ui.error("Opcion no valida."))
            except ValueError as error:
                self._pause(ui.error(str(error)))

    def _render_costs(self) -> None:
        ui.clear_screen()
        costs = self.cost_service.filter_costs()
        print(ui.title("ODIN CLI", "Modulo de costes"))
        print(
            ui.panel(
                "Costes",
                [
                    ui.table(
                        ["ID", "Nombre", "Tipo", "Importe", "Fecha"],
                        [
                            [cost.id, cost.name, cost.cost_type.value, cost.amount, cost.recorded_at]
                            for cost in costs
                        ],
                    )
                ],
            )
        )
        print(
            ui.menu(
                "Acciones",
                [
                    ("1", "Crear coste"),
                    ("2", "Editar coste"),
                    ("3", "Eliminar coste"),
                    ("4", "Filtrar costes"),
                    ("b", "Volver"),
                ],
            )
        )

    def _create_cost(self) -> None:
        name = self._ask_required("Nombre del coste")
        amount = self._ask_decimal("Importe")
        cost_type = self._ask_cost_type()
        cost = self.cost_service.create_cost(name=name, amount=amount, cost_type=cost_type)
        self._pause(ui.success(f"Coste creado con ID {cost.id}."))

    def _update_cost(self) -> None:
        cost = self._select_cost()
        print(
            ui.panel(
                "Coste actual",
                [
                    ui.key_value(
                        [
                            ("ID", cost.id),
                            ("Nombre", cost.name),
                            ("Tipo", cost.cost_type.value),
                            ("Importe", cost.amount),
                            ("Fecha", cost.recorded_at),
                        ]
                    )
                ],
            )
        )
        name = self._ask_optional_text("Nuevo nombre (enter para mantener)")
        amount = self._ask_optional_decimal("Nuevo importe (enter para mantener)")
        cost_type = self._ask_optional_cost_type()
        updated = self.cost_service.update_cost(
            cost.id,
            name=name or None,
            amount=amount,
            cost_type=cost_type,
        )
        self._pause(ui.success(f"Coste {updated.id} actualizado."))

    def _delete_cost(self) -> None:
        cost = self._select_cost()
        confirmed = self._ask(f"Escribe SI para eliminar '{cost.name}'")
        if confirmed != "SI":
            self._pause(ui.info("Operacion cancelada."))
            return
        self.cost_service.delete_cost(cost.id)
        self._pause(ui.success("Coste eliminado."))

    def _filter_costs(self) -> None:
        name = self._ask_optional_text("Texto a buscar")
        cost_type = self._ask_optional_cost_type()
        min_amount = self._ask_optional_decimal("Importe minimo (opcional)", allow_zero=True)
        max_amount = self._ask_optional_decimal("Importe maximo (opcional)", allow_zero=True)
        results = self.cost_service.filter_costs(
            name=name or None,
            cost_type=cost_type,
            min_amount=min_amount,
            max_amount=max_amount,
        )
        self._pause(
            ui.panel(
                "Resultados",
                [
                    ui.table(
                        ["ID", "Nombre", "Tipo", "Importe", "Fecha"],
                        [
                            [cost.id, cost.name, cost.cost_type.value, cost.amount, cost.recorded_at]
                            for cost in results
                        ],
                    )
                ],
            )
        )

    def _sales_menu(self) -> None:
        while True:
            ui.clear_screen()
            sales = self.sales_service.filter_sales()
            print(ui.title("ODIN CLI", "Modulo de ventas"))
            print(
                ui.panel(
                    "Ventas",
                    [
                        ui.table(
                            ["ID", "Producto", "Precio", "Fecha"],
                            [
                                [sale.id, f"{sale.product_id} - {sale.product_name}", sale.sale_price, sale.sale_date]
                                for sale in sales
                            ],
                        )
                    ],
                )
            )
            print(
                ui.menu(
                    "Acciones",
                    [
                        ("1", "Registrar venta"),
                        ("2", "Editar venta"),
                        ("3", "Eliminar venta"),
                        ("4", "Filtrar ventas"),
                        ("b", "Volver"),
                    ],
                )
            )
            option = self._ask("Elige una accion").lower()
            try:
                if option == "1":
                    self._create_sale()
                elif option == "2":
                    self._update_sale()
                elif option == "3":
                    self._delete_sale()
                elif option == "4":
                    self._filter_sales()
                elif option == "b":
                    return
                else:
                    self._pause(ui.error("Opcion no valida."))
            except ValueError as error:
                self._pause(ui.error(str(error)))

    def _create_sale(self) -> None:
        product = self._select_product()
        sale_price = self._ask_optional_decimal("Precio de venta (enter para usar el actual)")
        sale_date = self._ask_optional_text("Fecha ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)")
        sale = self.sales_service.create_sale(
            product.id,
            sale_price=sale_price,
            sale_date=sale_date or None,
        )
        self._pause(ui.success(f"Venta registrada con ID {sale.id}."))

    def _update_sale(self) -> None:
        sale = self._select_sale()
        print(ui.panel("Venta actual", [self._sale_detail(sale)]))
        sale_price = self._ask_optional_decimal("Nuevo precio (enter para mantener)")
        sale_date = self._ask_optional_text("Nueva fecha ISO (enter para mantener)")
        updated = self.sales_service.update_sale(
            sale.id,
            sale_price=sale_price,
            sale_date=sale_date or None,
        )
        self._pause(ui.success(f"Venta {updated.id} actualizada."))

    def _delete_sale(self) -> None:
        sale = self._select_sale()
        confirmed = self._ask(f"Escribe SI para eliminar la venta {sale.id}")
        if confirmed != "SI":
            self._pause(ui.info("Operacion cancelada."))
            return
        self.sales_service.delete_sale(sale.id)
        self._pause(ui.success("Venta eliminada."))

    def _filter_sales(self) -> None:
        product_name = self._ask_optional_text("Nombre del producto")
        sale_date = self._ask_optional_text("Fecha o prefijo de fecha")
        min_price = self._ask_optional_decimal("Precio minimo (opcional)", allow_zero=True)
        max_price = self._ask_optional_decimal("Precio maximo (opcional)", allow_zero=True)
        results = self.sales_service.filter_sales(
            product_name=product_name or None,
            sale_date=sale_date or None,
            min_sale_price=min_price,
            max_sale_price=max_price,
        )
        self._pause(
            ui.panel(
                "Resultados",
                [
                    ui.table(
                        ["ID", "Producto", "Precio", "Fecha"],
                        [
                            [sale.id, f"{sale.product_id} - {sale.product_name}", sale.sale_price, sale.sale_date]
                            for sale in results
                        ],
                    )
                ],
            )
        )

    def _stats_menu(self) -> None:
        month = self._ask_optional_text("Mes para consultar (YYYY-MM, enter para actual)") or None
        try:
            monthly_stats = self.stats_service.get_monthly_stats(month)
            coverage = monthly_stats.fixed_cost_coverage
            evolution = monthly_stats.profitability_evolution
            series = self.stats_service.get_profitability_series(monthly_stats.month, periods=6)
        except ValueError as error:
            self._pause(ui.error(str(error)))
            return

        self._pause(
            "\n".join(
                [
                    ui.title("ODIN CLI", f"Estadisticas de {monthly_stats.month}"),
                    ui.panel(
                        "Resumen financiero",
                        [
                            ui.key_value(
                                [
                                    ("Ingresos", monthly_stats.total_income),
                                    ("Costes fijos", monthly_stats.total_fixed_costs),
                                    ("Costes variables", monthly_stats.total_variable_costs),
                                    ("Margen", monthly_stats.total_margin),
                                    ("Rentabilidad", f"{monthly_stats.profitability:.2f}%"),
                                ]
                            )
                        ],
                    ),
                    ui.panel(
                        "Cobertura de costes fijos",
                        [
                            ui.key_value(
                                [
                                    ("Cubierto", coverage.covered_amount),
                                    ("Pendiente", coverage.uncovered_amount),
                                    ("Cobertura", f"{coverage.coverage_percentage:.2f}%"),
                                ]
                            )
                        ],
                    ),
                    ui.panel(
                        "Evolucion de rentabilidad",
                        [
                            ui.key_value(
                                [
                                    ("Mes actual", f"{evolution.current_profitability:.2f}%"),
                                    ("Mes anterior", f"{evolution.previous_profitability:.2f}%"),
                                    ("Cambio absoluto", f"{evolution.absolute_change:.2f}%"),
                                    (
                                        "Cambio porcentual",
                                        f"{evolution.percentage_change:.2f}%"
                                        if evolution.percentage_change is not None
                                        else "-",
                                    ),
                                ]
                            )
                        ],
                    ),
                    ui.panel(
                        "Serie de 6 meses",
                        [
                            ui.table(
                                ["Mes", "Rentabilidad"],
                                [[item["month"], f"{item['profitability']:.2f}%"] for item in series],
                            )
                        ],
                    ),
                ]
            )
        )

    def _select_product(self) -> Product:
        product_id = self._ask_int("ID del producto")
        return self.product_service.get_product(product_id)

    def _select_cost(self) -> Cost:
        cost_id = self._ask_int("ID del coste")
        return self.cost_service.get_cost(cost_id)

    def _select_sale(self) -> Sale:
        sale_id = self._ask_int("ID de la venta")
        return self.sales_service.get_sale(sale_id)

    def _product_detail(self, product: Product) -> str:
        variable_costs = self.product_service.list_variable_costs(product.id)
        return ui.key_value(
            [
                ("ID", product.id),
                ("Nombre", product.name),
                ("Coste variable", product.cost_price),
                ("Precio recomendado", product.recommended_price),
                ("Precio de venta", product.sale_price),
                (
                    "Costes asignados",
                    ", ".join(f"{cost.id}:{cost.name}" for cost in variable_costs) if variable_costs else "-",
                ),
            ]
        )

    @staticmethod
    def _sale_detail(sale: Sale) -> str:
        return ui.key_value(
            [
                ("ID", sale.id),
                ("Producto", f"{sale.product_id} - {sale.product_name}"),
                ("Precio", sale.sale_price),
                ("Fecha", sale.sale_date),
            ]
        )

    @staticmethod
    def _ask(label: str) -> str:
        return input(ui.prompt(label)).strip()

    def _ask_required(self, label: str) -> str:
        value = self._ask(label)
        if not value:
            raise ValueError(f"{label} no puede estar vacio.")
        return value

    def _ask_optional_text(self, label: str) -> str:
        return self._ask(label)

    def _ask_int(self, label: str) -> int:
        value = self._ask_required(label)
        try:
            return int(value)
        except ValueError as error:
            raise ValueError(f"{label} debe ser un numero entero.") from error

    def _ask_decimal(self, label: str, *, allow_zero: bool = False) -> Decimal:
        value = self._ask_required(label).replace(",", ".")
        try:
            amount = Decimal(value)
        except InvalidOperation as error:
            raise ValueError(f"{label} debe ser un numero valido.") from error
        if allow_zero:
            if amount < 0:
                raise ValueError(f"{label} no puede ser negativo.")
        elif amount <= 0:
            raise ValueError(f"{label} debe ser mayor que cero.")
        return amount

    def _ask_optional_decimal(self, label: str, *, allow_zero: bool = False) -> Decimal | None:
        value = self._ask(label)
        if not value:
            return None
        try:
            amount = Decimal(value.replace(",", "."))
        except InvalidOperation as error:
            raise ValueError(f"{label} debe ser un numero valido.") from error
        if allow_zero:
            if amount < 0:
                raise ValueError(f"{label} no puede ser negativo.")
        elif amount <= 0:
            raise ValueError(f"{label} debe ser mayor que cero.")
        return amount

    def _ask_cost_type(self) -> str:
        value = self._ask_required("Tipo de coste (fixed/variable)").lower()
        if value not in {"fixed", "variable"}:
            raise ValueError("El tipo de coste debe ser 'fixed' o 'variable'.")
        return value

    def _ask_optional_cost_type(self) -> str | None:
        value = self._ask("Tipo de coste (fixed/variable, enter para mantener)").lower()
        if not value:
            return None
        if value not in {"fixed", "variable"}:
            raise ValueError("El tipo de coste debe ser 'fixed' o 'variable'.")
        return value

    @staticmethod
    def _pause(message: str) -> None:
        print(message)
        input(ui.prompt("Pulsa enter para continuar"))


def run_cli() -> None:
    OdinCLIApp().run()
