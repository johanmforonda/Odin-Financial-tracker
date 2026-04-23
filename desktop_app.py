from __future__ import annotations

import tkinter as tk
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

from core.domain.cost_calculator import calculate_total_variable_cost
from core.domain.pricing import calculate_recommended_price, round_recommended_price
from core.models.cost import Cost, CostType
from core.models.product import Product
from main import build_services


BACKGROUND = "#a7a7b0"
SHELL = "#d9d9df"
PANEL = "#f8f8fb"
PANEL_ALT = "#ffffff"
TEXT = "#45454f"
MUTED = "#7b7b86"
ACCENT = "#ff8552"
ACCENT_DEEP = "#ff6b3d"
ACCENT_SOFT = "#ffe4db"
PINK = "#ff8d7d"
PURPLE = "#b945d6"
LINE = "#ececf2"


def format_currency(value: Decimal | float | int | str) -> str:
    amount = Decimal(str(value))
    return f"${amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def safe_decimal(raw_value: str) -> Decimal | None:
    cleaned = raw_value.strip().replace(".", "").replace(",", ".")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def today_prefix() -> str:
    return datetime.now(UTC).replace(tzinfo=None).strftime("%Y-%m-%d")


class HoverButton(tk.Button):
    def __init__(self, master: tk.Widget, *, bg: str, hover_bg: str, active_bg: str, **kwargs) -> None:
        super().__init__(master, bg=bg, activebackground=active_bg, bd=0, relief="flat", **kwargs)
        self.default_bg = bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self.bind("<Enter>", lambda _: self.configure(bg=self.hover_bg))
        self.bind("<Leave>", lambda _: self.configure(bg=self.default_bg))
        self.bind("<ButtonPress-1>", lambda _: self.configure(bg=self.active_bg))
        self.bind("<ButtonRelease-1>", lambda _: self.configure(bg=self.hover_bg))


class CardList(tk.Frame):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, bg=PANEL)
        self.canvas = tk.Canvas(self, bg=PANEL, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=PANEL)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.window, width=event.width))

    def clear(self) -> None:
        for child in self.inner.winfo_children():
            child.destroy()


class BaseModal(tk.Toplevel):
    def __init__(self, master: tk.Widget, title: str, size: str) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry(size)
        self.configure(bg=SHELL)
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        shell = tk.Frame(self, bg=SHELL, padx=18, pady=18)
        shell.pack(fill="both", expand=True)
        self.body = tk.Frame(shell, bg=PANEL_ALT, padx=22, pady=22)
        self.body.pack(fill="both", expand=True)
        tk.Label(self.body, text=title, font=("Segoe UI", 18, "bold"), bg=PANEL_ALT, fg=TEXT).pack(anchor="w", pady=(0, 14))

    def field(self, label: str) -> tk.Frame:
        wrapper = tk.Frame(self.body, bg=PANEL_ALT)
        wrapper.pack(fill="x", pady=8)
        tk.Label(wrapper, text=label, font=("Segoe UI", 10, "bold"), bg=PANEL_ALT, fg=TEXT).pack(anchor="w")
        return wrapper


class OdinDesktopApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Odin Finance")
        self.geometry("1440x920")
        self.minsize(1320, 840)
        self.configure(bg=BACKGROUND)

        (
            self.product_service,
            self.cost_service,
            self.pricing_service,
            self.sales_service,
            self.stats_service,
        ) = build_services()

        self.active_tab = "products"
        self.sidebar_buttons: dict[str, HoverButton] = {}
        self.frames: dict[str, tk.Frame] = {}
        self.product_filters = {"name": "", "min_sale_price": "", "max_sale_price": ""}
        self.variable_filters = {"name": ""}
        self.fixed_filters = {"name": ""}
        self.selected_month = tk.StringVar(value=self.month_options(8)[0])
        self.product_form_visible = False
        self.product_form_product: Product | None = None
        self.product_form_costs: list[Cost] = []
        self.product_form_cost_vars: dict[int, tk.BooleanVar] = {}

        self._build_shell()
        self.show_tab("products")

    def _build_shell(self) -> None:
        shell = tk.Frame(self, bg=SHELL, padx=30, pady=30)
        shell.pack(fill="both", expand=True, padx=38, pady=36)

        sidebar = tk.Frame(shell, bg=PANEL, width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=PANEL)
        brand.pack(fill="x", padx=24, pady=(24, 20))
        self.brand_symbol = tk.Canvas(brand, width=76, height=76, bg=PANEL, highlightthickness=0)
        self.brand_symbol.pack(anchor="w")
        self.draw_brand_symbol()
        tk.Label(brand, text="Odin", font=("Segoe UI", 26, "bold"), bg=PANEL, fg=TEXT).pack(anchor="w", pady=(10, 0))
        tk.Label(brand, text="Simbolo integrado en la app", bg=PANEL, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        for label, key in (
            ("Productos", "products"),
            ("Costes Variables", "variable_costs"),
            ("Costes Fijos", "fixed_costs"),
            ("Stats", "stats"),
        ):
            button = HoverButton(
                sidebar,
                text=label,
                command=lambda item=key: self.show_tab(item),
                bg=PANEL,
                hover_bg=ACCENT_SOFT,
                active_bg=ACCENT_SOFT,
                fg=TEXT,
                activeforeground=TEXT,
                font=("Segoe UI", 13, "bold"),
                anchor="w",
                padx=22,
                pady=16,
                cursor="hand2",
            )
            button.pack(fill="x", padx=18, pady=6)
            self.sidebar_buttons[key] = button

        tk.Label(sidebar, text="Desktop UI ready for .exe / .app", bg=PANEL, fg=MUTED, font=("Segoe UI", 10)).pack(side="bottom", anchor="w", padx=28, pady=26)

        content = tk.Frame(shell, bg=SHELL)
        content.pack(side="left", fill="both", expand=True, padx=(24, 0))

        for key in ("products", "variable_costs", "fixed_costs", "stats"):
            frame = tk.Frame(content, bg=SHELL)
            self.frames[key] = frame

        self._build_products_tab(self.frames["products"])
        self._build_costs_tab(self.frames["variable_costs"], "variable")
        self._build_costs_tab(self.frames["fixed_costs"], "fixed")
        self._build_stats_tab(self.frames["stats"])

    def draw_brand_symbol(self) -> None:
        canvas = self.brand_symbol
        canvas.delete("all")
        stroke = "#121212"
        glow = "#2a2a30"
        highlight = "#f7f7fa"
        arcs = (
            (9, 8, 57, 56, 18),
            (22, 18, 70, 66, 138),
            (5, 25, 53, 73, 258),
        )
        for x0, y0, x1, y1, start in arcs:
            canvas.create_arc(x0, y0, x1, y1, start=start, extent=230, style="arc", outline=stroke, width=10)
        for cx, cy in ((18, 18), (57, 18), (37, 58)):
            canvas.create_oval(cx - 7, cy - 7, cx + 7, cy + 7, fill=glow, outline="")
            canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=highlight, outline="")
        canvas.create_line(5, 5, 71, 71, fill=highlight, width=2)
        canvas.create_line(71, 5, 5, 71, fill=highlight, width=2)

    def month_options(self, count: int) -> list[str]:
        values = []
        cursor = datetime.now(UTC).replace(tzinfo=None)
        for _ in range(count):
            values.append(cursor.strftime("%Y-%m"))
            if cursor.month == 1:
                cursor = cursor.replace(year=cursor.year - 1, month=12)
            else:
                cursor = cursor.replace(month=cursor.month - 1)
        return values

    def show_tab(self, tab_name: str) -> None:
        self.active_tab = tab_name
        for key, button in self.sidebar_buttons.items():
            button.configure(bg=ACCENT_SOFT if key == tab_name else PANEL)
        for key, frame in self.frames.items():
            frame.pack_forget()
            if key == tab_name:
                frame.pack(fill="both", expand=True)
        if tab_name == "products":
            self.refresh_products()
        elif tab_name == "variable_costs":
            self.refresh_costs("variable")
        elif tab_name == "fixed_costs":
            self.refresh_costs("fixed")
        elif tab_name == "stats":
            self.refresh_stats()

    def build_header(self, parent: tk.Widget, title: str, subtitle: str) -> tk.Frame:
        wrapper = tk.Frame(parent, bg=SHELL)
        wrapper.pack(fill="x", pady=(0, 18))
        text = tk.Frame(wrapper, bg=SHELL)
        text.pack(side="left")
        tk.Label(text, text=title, font=("Segoe UI", 27, "bold"), bg=SHELL, fg=TEXT).pack(anchor="w")
        tk.Label(text, text=subtitle, font=("Segoe UI", 11), bg=SHELL, fg=MUTED).pack(anchor="w", pady=(4, 0))
        return wrapper

    def _build_products_tab(self, parent: tk.Frame) -> None:
        header = self.build_header(parent, "Productos", "Catalogo visual con venta rapida, filtros y edicion por clic.")
        self.sales_today_label = tk.Label(header, text="Ventas del dia\n$0", justify="left", bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 14, "bold"), padx=18, pady=16)
        self.sales_today_label.pack(side="left", padx=(24, 12))
        controls = tk.Frame(header, bg=SHELL)
        controls.pack(side="right")
        HoverButton(controls, text="Filtrar", command=self.open_product_filter_modal, bg=PANEL_ALT, hover_bg=ACCENT_SOFT, active_bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="left", padx=8)
        self.product_form_button = HoverButton(controls, text="+ Anadir producto", command=self.open_product_modal, bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2")
        self.product_form_button.pack(side="left", padx=8)

        self.product_form_panel = tk.Frame(parent, bg=PANEL_ALT, padx=22, pady=22)
        self._build_product_form_panel()

        self.products_list = CardList(parent)
        self.products_list.pack(fill="both", expand=True)

    def _build_product_form_panel(self) -> None:
        self.product_form_name_var = tk.StringVar()
        self.product_form_minimum_revenue_var = tk.StringVar()
        self.product_form_sale_price_var = tk.StringVar()
        self.product_form_name_var.trace_add("write", lambda *_: self.update_product_form_preview())
        self.product_form_minimum_revenue_var.trace_add("write", lambda *_: self.update_product_form_preview())
        self.product_form_sale_price_var.trace_add("write", lambda *_: self.update_product_form_preview())

        header = tk.Frame(self.product_form_panel, bg=PANEL_ALT)
        header.pack(fill="x")
        header_text = tk.Frame(header, bg=PANEL_ALT)
        header_text.pack(side="left", fill="x", expand=True)
        self.product_form_title = tk.Label(header_text, text="Anadir producto", font=("Segoe UI", 18, "bold"), bg=PANEL_ALT, fg=TEXT)
        self.product_form_title.pack(anchor="w")
        tk.Label(header_text, text="Calculamos el recomendado antes de pedir el precio de venta.", font=("Segoe UI", 10), bg=PANEL_ALT, fg=MUTED).pack(anchor="w", pady=(4, 0))
        HoverButton(header, text="Cerrar", command=self.hide_product_form, bg=SHELL, hover_bg=ACCENT_SOFT, active_bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 10, "bold"), padx=14, pady=8, cursor="hand2").pack(side="right")

        form = tk.Frame(self.product_form_panel, bg=PANEL_ALT)
        form.pack(fill="x", pady=(20, 0))

        self.build_inline_field(form, "Nombre", self.product_form_name_var)
        self.build_inline_field(form, "Ingreso minimo del mes", self.product_form_minimum_revenue_var)

        metrics = tk.Frame(form, bg=PANEL_ALT)
        metrics.pack(fill="x", pady=(6, 8))
        self.product_form_cost_card = tk.Label(metrics, text="Coste variable\n$0", justify="left", bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 13, "bold"), padx=18, pady=16)
        self.product_form_cost_card.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.product_form_recommended_card = tk.Label(metrics, text="Recomendado\n--", justify="left", bg=PANEL, fg=TEXT, font=("Segoe UI", 13, "bold"), padx=18, pady=16)
        self.product_form_recommended_card.pack(side="left", fill="x", expand=True, padx=(8, 0))

        self.product_form_feedback = tk.Label(form, text="Selecciona costes y un ingreso minimo para calcular el recomendado.", bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 10))
        self.product_form_feedback.pack(anchor="w", pady=(0, 10))

        costs_wrapper = tk.Frame(form, bg=PANEL_ALT)
        costs_wrapper.pack(fill="x", pady=(4, 10))
        tk.Label(costs_wrapper, text="Costes variables", font=("Segoe UI", 10, "bold"), bg=PANEL_ALT, fg=TEXT).pack(anchor="w")
        self.product_form_cost_grid = tk.Frame(costs_wrapper, bg=PANEL_ALT)
        self.product_form_cost_grid.pack(fill="x", pady=(8, 0))

        sale_row = tk.Frame(form, bg=PANEL_ALT)
        sale_row.pack(fill="x", pady=(4, 0))
        sale_header = tk.Frame(sale_row, bg=PANEL_ALT)
        sale_header.pack(fill="x")
        tk.Label(sale_header, text="Precio de venta", font=("Segoe UI", 10, "bold"), bg=PANEL_ALT, fg=TEXT).pack(side="left")
        HoverButton(sale_header, text="Usar recomendado", command=self.use_recommended_sale_price, bg=PANEL, hover_bg=ACCENT_SOFT, active_bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 9, "bold"), padx=12, pady=6, cursor="hand2").pack(side="right")
        tk.Entry(sale_row, textvariable=self.product_form_sale_price_var, font=("Segoe UI", 12), relief="flat", bd=0, bg=SHELL, fg=TEXT).pack(fill="x", pady=(6, 0), ipady=10)

        footer = tk.Frame(self.product_form_panel, bg=PANEL_ALT)
        footer.pack(fill="x", pady=(18, 0))
        HoverButton(footer, text="Cancelar", command=self.hide_product_form, bg=SHELL, hover_bg=ACCENT_SOFT, active_bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="right", padx=6)
        HoverButton(footer, text="Guardar", command=self.submit_product_form, bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="right", padx=6)

    def build_inline_field(self, parent: tk.Widget, label: str, variable: tk.StringVar) -> None:
        wrapper = tk.Frame(parent, bg=PANEL_ALT)
        wrapper.pack(fill="x", pady=8)
        tk.Label(wrapper, text=label, font=("Segoe UI", 10, "bold"), bg=PANEL_ALT, fg=TEXT).pack(anchor="w")
        tk.Entry(wrapper, textvariable=variable, font=("Segoe UI", 12), relief="flat", bd=0, bg=SHELL, fg=TEXT).pack(fill="x", pady=(6, 0), ipady=10)

    def _build_costs_tab(self, parent: tk.Frame, cost_type: str) -> None:
        titles = {
            "variable": ("Costes Variables", "Anade o ajusta los costes que se asignan a cada producto."),
            "fixed": ("Costes Fijos", "Costes mensuales con opcion rapida para anadirlos de nuevo."),
        }
        header = self.build_header(parent, titles[cost_type][0], titles[cost_type][1])
        controls = tk.Frame(header, bg=SHELL)
        controls.pack(side="right")
        HoverButton(controls, text="Filtrar", command=lambda kind=cost_type: self.open_cost_filter_modal(kind), bg=PANEL_ALT, hover_bg=ACCENT_SOFT, active_bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="left", padx=8)
        HoverButton(controls, text="+ Anadir", command=lambda kind=cost_type: self.open_cost_modal(kind), bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="left", padx=8)
        cost_list = CardList(parent)
        cost_list.pack(fill="both", expand=True)
        if cost_type == "variable":
            self.variable_cost_list = cost_list
        else:
            self.fixed_cost_list = cost_list

    def _build_stats_tab(self, parent: tk.Frame) -> None:
        header = self.build_header(parent, "Stats", "Rentabilidad, comparacion intermensual y cobertura operativa del mes.")
        controls = tk.Frame(header, bg=SHELL)
        controls.pack(side="right")
        month_picker = ttk.Combobox(controls, values=self.month_options(8), textvariable=self.selected_month, width=10, state="readonly")
        month_picker.pack(side="left", padx=8)
        month_picker.bind("<<ComboboxSelected>>", lambda _: self.refresh_stats())
        HoverButton(controls, text="Actualizar", command=self.refresh_stats, bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="left", padx=8)

        self.stats_cards_row = tk.Frame(parent, bg=SHELL)
        self.stats_cards_row.pack(fill="x", pady=(0, 18))
        self.stats_card_labels: dict[str, tk.Label] = {}
        for key, title in (("income", "Ingresos"), ("variable", "Variables"), ("fixed", "Fijos"), ("profitability", "Rentabilidad")):
            card = tk.Label(self.stats_cards_row, text=f"{title}\n$0", justify="left", bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 14, "bold"), padx=18, pady=18)
            card.pack(side="left", fill="x", expand=True, padx=8)
            self.stats_card_labels[key] = card

        self.coverage_frame = tk.Frame(parent, bg=PANEL_ALT, padx=18, pady=18)
        self.coverage_frame.pack(fill="x", pady=(0, 18))
        tk.Label(self.coverage_frame, text="Cobertura de costes fijos", bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(self.coverage_frame, text="Que parte del margen ya absorbio el coste fijo del mes.", bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 10))
        self.coverage_canvas = tk.Canvas(self.coverage_frame, height=84, bg=PANEL_ALT, highlightthickness=0)
        self.coverage_canvas.pack(fill="x")

        charts = tk.Frame(parent, bg=SHELL)
        charts.pack(fill="both", expand=True)
        self.line_panel = tk.Frame(charts, bg=PANEL_ALT, padx=18, pady=18)
        self.line_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(self.line_panel, text="Evolucion intermensual", bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        self.line_chart = tk.Canvas(self.line_panel, bg=PANEL_ALT, height=290, highlightthickness=0)
        self.line_chart.pack(fill="both", expand=True, pady=(10, 0))

        self.right_stats = tk.Frame(charts, bg=SHELL)
        self.right_stats.pack(side="left", fill="y", padx=(10, 0))
        self.delta_card = tk.Label(self.right_stats, text="Cambio\n$0", justify="left", bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 13, "bold"), padx=18, pady=18)
        self.delta_card.pack(fill="x", pady=(0, 12))
        self.bar_panel = tk.Frame(self.right_stats, bg=PANEL_ALT, padx=18, pady=18)
        self.bar_panel.pack(fill="both", expand=True)
        tk.Label(self.bar_panel, text="Pulso del mes", bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        self.bar_chart = tk.Canvas(self.bar_panel, bg=PANEL_ALT, width=320, height=250, highlightthickness=0)
        self.bar_chart.pack(fill="both", expand=True, pady=(10, 0))

    def refresh_products(self) -> None:
        self.products_list.clear()
        products = self.product_service.filter_products(
            name=self.product_filters["name"] or None,
            min_sale_price=safe_decimal(self.product_filters["min_sale_price"]) if self.product_filters["min_sale_price"] else None,
            max_sale_price=safe_decimal(self.product_filters["max_sale_price"]) if self.product_filters["max_sale_price"] else None,
        )
        sales_today = self.sales_service.filter_sales(sale_date=today_prefix())
        total_sales = sum((sale.sale_price for sale in sales_today), start=Decimal("0.00"))
        self.sales_today_label.configure(text=f"Ventas del dia\n{format_currency(total_sales)}")

        if not products:
            tk.Label(self.products_list.inner, text="No hay productos para mostrar.", bg=PANEL, fg=MUTED, font=("Segoe UI", 12, "bold")).pack(pady=24)
            return

        for product in products:
            self.render_product_card(product)

    def render_product_card(self, product: Product) -> None:
        card = tk.Frame(self.products_list.inner, bg=PANEL_ALT, padx=18, pady=18)
        card.pack(fill="x", pady=10)
        left = tk.Frame(card, bg=PANEL_ALT)
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text=product.name, bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(
            left,
            text=f"Venta {format_currency(product.sale_price)}   ·   Recomendado {format_currency(product.recommended_price)}   ·   Coste {format_currency(product.cost_price)}",
            bg=PANEL_ALT,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 10))
        tags = tk.Frame(left, bg=PANEL_ALT)
        tags.pack(anchor="w")
        for cost in self.product_service.list_variable_costs(product.id):
            tk.Label(tags, text=cost.name, bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 9, "bold"), padx=10, pady=5).pack(side="left", padx=(0, 8))

        actions = tk.Frame(card, bg=PANEL_ALT)
        actions.pack(side="right", anchor="n")
        HoverButton(actions, text="Vender", command=lambda item=product: self.open_sell_modal(item), bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 10, "bold"), padx=16, pady=10, cursor="hand2").pack(side="left", padx=8)

        menu_button = tk.Menubutton(actions, text="⋯", bg=PANEL_ALT, fg=TEXT, relief="flat", bd=0, padx=14, pady=10, font=("Segoe UI", 12, "bold"), cursor="hand2")
        menu = tk.Menu(menu_button, tearoff=False, bg=PANEL_ALT, fg=TEXT, activebackground=ACCENT_SOFT)
        menu.add_command(label="Editar", command=lambda item=product: self.open_product_modal(item))
        menu.add_command(label="Gestionar costes", command=lambda item=product: self.open_product_modal(item))
        menu.add_separator()
        menu.add_command(label="Eliminar", command=lambda item=product: self.delete_product(item))
        menu_button.configure(menu=menu)
        menu_button.pack(side="left")

    def refresh_costs(self, cost_type: str) -> None:
        target = self.variable_cost_list if cost_type == "variable" else self.fixed_cost_list
        target.clear()
        filters = self.variable_filters if cost_type == "variable" else self.fixed_filters
        costs = self.cost_service.filter_costs(name=filters["name"] or None, cost_type=cost_type)
        if not costs:
            tk.Label(target.inner, text="No hay costes para mostrar.", bg=PANEL, fg=MUTED, font=("Segoe UI", 12, "bold")).pack(pady=24)
            return
        for cost in costs:
            card = tk.Frame(target.inner, bg=PANEL_ALT, padx=18, pady=18)
            card.pack(fill="x", pady=10)
            left = tk.Frame(card, bg=PANEL_ALT)
            left.pack(side="left", fill="both", expand=True)
            tk.Label(left, text=cost.name, bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(anchor="w")
            tk.Label(left, text=f"{format_currency(cost.amount)}   ·   {cost.recorded_at[:10]}", bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
            menu_button = tk.Menubutton(card, text="Acciones", bg=PANEL_ALT, fg=TEXT, relief="flat", bd=0, padx=14, pady=10, font=("Segoe UI", 10, "bold"), cursor="hand2")
            menu = tk.Menu(menu_button, tearoff=False, bg=PANEL_ALT, fg=TEXT, activebackground=ACCENT_SOFT)
            menu.add_command(label="Editar", command=lambda item=cost, kind=cost_type: self.open_cost_modal(kind, item))
            if cost_type == "fixed":
                menu.add_command(label="Anadir de nuevo este mes", command=lambda item=cost: self.renew_fixed_cost(item))
            menu.add_separator()
            menu.add_command(label="Eliminar", command=lambda item=cost, kind=cost_type: self.delete_cost(item, kind))
            menu_button.configure(menu=menu)
            menu_button.pack(side="right")

    def refresh_stats(self) -> None:
        month = self.selected_month.get() or None
        snapshot = self.stats_service.get_monthly_stats_as_dict(month)
        self.stats_card_labels["income"].configure(text=f"Ingresos\n{format_currency(snapshot['total_income'])}")
        self.stats_card_labels["variable"].configure(text=f"Variables\n{format_currency(snapshot['total_variable_costs'])}")
        self.stats_card_labels["fixed"].configure(text=f"Fijos\n{format_currency(snapshot['total_fixed_costs'])}")
        self.stats_card_labels["profitability"].configure(text=f"Rentabilidad\n{format_currency(snapshot['profitability'])}")
        self.draw_coverage(snapshot["fixed_cost_coverage"])
        self.draw_line_chart(self.stats_service.get_profitability_series(month, periods=6))
        self.draw_bar_chart(snapshot)
        evolution = snapshot["profitability_evolution"]
        delta = evolution["absolute_change"]
        percentage = evolution["percentage_change"]
        suffix = "sin base previa" if percentage is None else f"{percentage}%"
        self.delta_card.configure(text=f"Cambio intermensual\n{format_currency(delta)}\n{suffix}")

    def draw_coverage(self, coverage: dict[str, Decimal]) -> None:
        self.coverage_canvas.delete("all")
        width = max(self.coverage_canvas.winfo_width(), 680)
        x0, y0, x1, y1 = 20, 24, width - 20, 50
        self.coverage_canvas.create_rectangle(x0, y0, x1, y1, fill=LINE, outline="")
        percentage = float(min(coverage["coverage_percentage"], Decimal("100")))
        self.animate_fill(x0, y0, x1, y1, percentage, 0)
        self.coverage_canvas.create_text(x0, y1 + 18, anchor="w", text=f"Cubierto {format_currency(coverage['covered_amount'])}", fill=TEXT, font=("Segoe UI", 10, "bold"))
        self.coverage_canvas.create_text(x1, y1 + 18, anchor="e", text=f"Falta {format_currency(coverage['uncovered_amount'])}", fill=MUTED, font=("Segoe UI", 10, "bold"))

    def animate_fill(self, x0: float, y0: float, x1: float, y1: float, target: float, frame: int) -> None:
        progress = min(frame / 18, 1)
        current_x = x0 + ((x1 - x0) * target / 100) * progress
        self.coverage_canvas.delete("fill")
        self.coverage_canvas.create_rectangle(x0, y0, current_x, y1, fill=ACCENT, outline="", tags="fill")
        if progress < 1:
            self.after(22, lambda: self.animate_fill(x0, y0, x1, y1, target, frame + 1))

    def draw_line_chart(self, series: list[dict[str, Decimal | str | None]]) -> None:
        self.line_chart.delete("all")
        width = max(self.line_chart.winfo_width(), 720)
        height = max(self.line_chart.winfo_height(), 300)
        left, top, right, bottom = 56, 20, width - 24, height - 36
        values = [item["profitability"] for item in series]
        if not values:
            return
        max_value = max(max(values), Decimal("1"))
        min_value = min(min(values), Decimal("0"))
        spread = max(max_value - min_value, Decimal("1"))
        for step in range(5):
            y = top + ((bottom - top) / 4) * step
            self.line_chart.create_line(left, y, right, y, fill=LINE, width=1)
        points = []
        for index, item in enumerate(series):
            x = left + ((right - left) / max(len(series) - 1, 1)) * index
            normalized = float((item["profitability"] - min_value) / spread)
            y = bottom - normalized * (bottom - top)
            points.append((x, y))
            self.line_chart.create_text(x, bottom + 18, text=str(item["month"])[5:], fill=MUTED, font=("Segoe UI", 9, "bold"))
        self.animate_line(points, 0)

    def animate_line(self, points: list[tuple[float, float]], index: int) -> None:
        if index >= len(points):
            return
        if index > 0:
            x1, y1 = points[index - 1]
            x2, y2 = points[index]
            self.line_chart.create_line(x1, y1, x2, y2, fill=ACCENT, width=3, smooth=True)
        x, y = points[index]
        self.line_chart.create_oval(x - 5, y - 5, x + 5, y + 5, fill=ACCENT, outline=PANEL_ALT, width=2)
        self.after(80, lambda: self.animate_line(points, index + 1))

    def draw_bar_chart(self, snapshot: dict[str, object]) -> None:
        self.bar_chart.delete("all")
        dataset = [("Ingresos", snapshot["total_income"], ACCENT), ("Variables", snapshot["total_variable_costs"], PINK), ("Fijos", snapshot["total_fixed_costs"], PURPLE)]
        width = max(self.bar_chart.winfo_width(), 320)
        height = max(self.bar_chart.winfo_height(), 240)
        base_y = height - 28
        max_value = max(max(item[1] for item in dataset), Decimal("1"))
        for index, (label, value, color) in enumerate(dataset):
            bar_x = 36 + index * 90
            target_height = float((value / max_value) * 150)
            self.animate_bar(bar_x, base_y, 48, target_height, color, 0)
            self.bar_chart.create_text(bar_x + 24, base_y + 16, text=label, fill=MUTED, font=("Segoe UI", 9, "bold"))
            self.bar_chart.create_text(bar_x + 24, base_y - target_height - 12, text=format_currency(value), fill=TEXT, font=("Segoe UI", 9, "bold"))

    def animate_bar(self, x: float, base_y: float, width: float, target_height: float, color: str, frame: int) -> None:
        progress = min(frame / 12, 1)
        current_height = target_height * progress
        tag = f"bar-{x}"
        self.bar_chart.delete(tag)
        self.bar_chart.create_rectangle(x, base_y - current_height, x + width, base_y, fill=color, outline="", tags=tag)
        if progress < 1:
            self.after(24, lambda: self.animate_bar(x, base_y, width, target_height, color, frame + 1))

    def open_product_modal(self, product: Product | None = None) -> None:
        self.product_form_product = product
        self.product_form_title.configure(text="Anadir producto" if product is None else f"Editar {product.name}")
        self.product_form_name_var.set("" if product is None else product.name)
        self.product_form_sale_price_var.set("" if product is None or product.sale_price == 0 else str(product.sale_price))
        self.product_form_minimum_revenue_var.set(self.estimate_minimum_revenue(product))
        self.product_form_costs = self.cost_service.filter_costs(cost_type="variable")
        self.product_form_cost_vars = {}

        assigned_ids = {cost.id for cost in self.product_service.list_variable_costs(product.id)} if product else set()
        for child in self.product_form_cost_grid.winfo_children():
            child.destroy()

        if not self.product_form_costs:
            tk.Label(self.product_form_cost_grid, text="No hay costes variables creados todavia.", bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w")
        else:
            for index, cost in enumerate(self.product_form_costs):
                variable = tk.BooleanVar(value=cost.id in assigned_ids)
                variable.trace_add("write", lambda *_: self.update_product_form_preview())
                self.product_form_cost_vars[cost.id] = variable
                tk.Checkbutton(
                    self.product_form_cost_grid,
                    text=f"{cost.name} · {format_currency(cost.amount)}",
                    variable=variable,
                    bg=PANEL_ALT,
                    fg=TEXT,
                    activebackground=PANEL_ALT,
                    selectcolor=ACCENT_SOFT,
                    font=("Segoe UI", 10, "bold"),
                    anchor="w",
                ).grid(row=index // 2, column=index % 2, sticky="w", padx=6, pady=6)

        if not self.product_form_visible:
            self.product_form_panel.pack(fill="x", pady=(0, 18), before=self.products_list)
            self.product_form_visible = True
        self.product_form_button.configure(text="Ocultar panel")
        self.update_product_form_preview()

    def hide_product_form(self) -> None:
        if self.product_form_visible:
            self.product_form_panel.pack_forget()
        self.product_form_visible = False
        self.product_form_product = None
        self.product_form_button.configure(text="+ Anadir producto")

    def current_fixed_costs_total(self) -> Decimal:
        current_month = datetime.now(UTC).replace(tzinfo=None).strftime("%Y-%m")
        fixed_costs = self.pricing_service.cost_repository.filter(
            {
                "cost_type": CostType.FIXED,
                "recorded_at_from": f"{current_month}-01T00:00:00",
                "recorded_at_to": self.pricing_service._build_next_month_start(current_month),
            }
        )
        return sum((cost.amount for cost in fixed_costs), start=Decimal("0.00"))

    def estimate_minimum_revenue(self, product: Product | None) -> str:
        if product is None or product.recommended_price <= 0 or product.cost_price <= 0:
            return ""
        margin = Decimal("1") - (product.cost_price / product.recommended_price)
        if margin <= 0:
            return ""
        fixed_costs = self.current_fixed_costs_total()
        if fixed_costs <= 0:
            return ""
        estimated = (fixed_costs / margin).quantize(Decimal("0.01"))
        return str(estimated)

    def get_product_form_totals(self) -> tuple[Decimal, Decimal | None, str]:
        selected_amounts = [
            cost.amount
            for cost in self.product_form_costs
            if self.product_form_cost_vars.get(cost.id) and self.product_form_cost_vars[cost.id].get()
        ]
        variable_total = calculate_total_variable_cost(selected_amounts)
        minimum_revenue = safe_decimal(self.product_form_minimum_revenue_var.get())
        if minimum_revenue is None:
            return variable_total, None, "Introduce el ingreso minimo mensual para calcular el recomendado."
        if minimum_revenue <= 0:
            return variable_total, None, "El ingreso minimo debe ser mayor que cero."
        try:
            margin = self.pricing_service.calculate_margin(minimum_revenue)
            recommended = round_recommended_price(calculate_recommended_price(variable_total, margin))
        except Exception as error:
            return variable_total, None, str(error)
        return variable_total, recommended, "Precio recomendado calculado."

    def update_product_form_preview(self) -> None:
        if not hasattr(self, "product_form_cost_card"):
            return
        variable_total, recommended, feedback = self.get_product_form_totals()
        self.product_form_cost_card.configure(text=f"Coste variable\n{format_currency(variable_total)}")
        if recommended is None:
            self.product_form_recommended_card.configure(text="Recomendado\n--")
            self.product_form_feedback.configure(text=feedback, fg=MUTED)
            return

        self.product_form_recommended_card.configure(text=f"Recomendado\n{format_currency(recommended)}")
        sale_price = safe_decimal(self.product_form_sale_price_var.get())
        if sale_price is None:
            feedback = f"Calculado. Puedes usar {format_currency(recommended)} como precio de venta."
            color = TEXT
        elif sale_price <= 0:
            feedback = "El precio de venta debe ser mayor que cero."
            color = MUTED
        elif sale_price < recommended:
            feedback = f"El precio de venta queda por debajo del recomendado ({format_currency(recommended)})."
            color = TEXT
        else:
            feedback = f"El precio de venta esta alineado o por encima del recomendado ({format_currency(recommended)})."
            color = TEXT
        self.product_form_feedback.configure(text=feedback, fg=color)

    def use_recommended_sale_price(self) -> None:
        _, recommended, _ = self.get_product_form_totals()
        if recommended is not None:
            self.product_form_sale_price_var.set(str(recommended))

    def submit_product_form(self) -> None:
        name = self.product_form_name_var.get().strip()
        if not name:
            messagebox.showerror("Producto", "Necesitas un nombre.")
            return

        minimum_revenue = safe_decimal(self.product_form_minimum_revenue_var.get())
        if minimum_revenue is None or minimum_revenue <= 0:
            messagebox.showerror("Producto", "Necesitas un ingreso minimo valido para calcular el recomendado.")
            return

        _, recommended, _ = self.get_product_form_totals()
        if recommended is None:
            messagebox.showerror("Producto", "No se pudo calcular el precio recomendado.")
            return

        sale_text = self.product_form_sale_price_var.get().strip()
        sale_price = safe_decimal(sale_text) if sale_text else recommended
        if sale_price is None or sale_price <= 0:
            messagebox.showerror("Producto", "Necesitas un precio de venta valido.")
            return

        selected_ids = {cost_id for cost_id, variable in self.product_form_cost_vars.items() if variable.get()}
        try:
            if self.product_form_product is None:
                target_product = self.product_service.create_product(name=name, sale_price=recommended)
                for cost_id in selected_ids:
                    self.product_service.add_variable_cost(target_product.id, cost_id)
            else:
                target_product = self.product_form_product
                current_ids = {cost.id for cost in self.product_service.list_variable_costs(target_product.id)}
                for cost_id in selected_ids - current_ids:
                    self.product_service.add_variable_cost(target_product.id, cost_id)
                for cost_id in current_ids - selected_ids:
                    self.product_service.remove_variable_cost(target_product.id, cost_id)

            priced_product = self.pricing_service.recommend_price(target_product.id, minimum_revenue=minimum_revenue)
            final_sale_price = sale_price or priced_product.recommended_price
            self.product_service.update_product(target_product.id, name=name, sale_price=final_sale_price)
            self.hide_product_form()
            self.refresh_products()
            self.refresh_stats()
        except Exception as error:
            messagebox.showerror("Producto", str(error))

    def open_sell_modal(self, product: Product) -> None:
        modal = BaseModal(self, f"Vender {product.name}", "420x280")
        sale_price_var = tk.StringVar(value=str(product.sale_price))
        tk.Entry(modal.field("Precio de venta"), textvariable=sale_price_var, font=("Segoe UI", 14, "bold"), relief="flat", bd=0, bg=SHELL, fg=TEXT).pack(fill="x", pady=(8, 0), ipady=10)

        quick = tk.Frame(modal.body, bg=PANEL_ALT)
        quick.pack(fill="x", pady=12)
        for delta in (-100, -50, 50, 100):
            HoverButton(
                quick,
                text=f"{delta:+}",
                command=lambda change=delta: sale_price_var.set(str((safe_decimal(sale_price_var.get()) or Decimal("0")) + Decimal(change))),
                bg=SHELL,
                hover_bg=ACCENT_SOFT,
                active_bg=ACCENT_SOFT,
                fg=TEXT,
                font=("Segoe UI", 10, "bold"),
                padx=14,
                pady=8,
                cursor="hand2",
            ).pack(side="left", padx=6)

        def confirm() -> None:
            sale_price = safe_decimal(sale_price_var.get())
            if sale_price is None:
                messagebox.showerror("Venta", "Necesitas un precio valido.")
                return
            try:
                self.sales_service.create_sale(product.id, sale_price=sale_price)
                modal.destroy()
                self.refresh_products()
            except Exception as error:
                messagebox.showerror("Venta", str(error))

        footer = tk.Frame(modal.body, bg=PANEL_ALT)
        footer.pack(fill="x", pady=(18, 0))
        HoverButton(footer, text="Cancelar", command=modal.destroy, bg=SHELL, hover_bg=ACCENT_SOFT, active_bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="right", padx=6)
        HoverButton(footer, text="Confirmar", command=confirm, bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="right", padx=6)

    def open_cost_modal(self, cost_type: str, cost: Cost | None = None) -> None:
        modal = BaseModal(self, "Anadir coste" if cost is None else "Editar coste", "430x320")
        name_var = tk.StringVar(value="" if cost is None else cost.name)
        amount_var = tk.StringVar(value="" if cost is None else str(cost.amount))
        tk.Entry(modal.field("Nombre"), textvariable=name_var, font=("Segoe UI", 12), relief="flat", bd=0, bg=SHELL, fg=TEXT).pack(fill="x", pady=(6, 0), ipady=10)
        tk.Entry(modal.field("Importe"), textvariable=amount_var, font=("Segoe UI", 12), relief="flat", bd=0, bg=SHELL, fg=TEXT).pack(fill="x", pady=(6, 0), ipady=10)

        def submit() -> None:
            amount = safe_decimal(amount_var.get())
            if not name_var.get().strip() or amount is None:
                messagebox.showerror("Costes", "Completa nombre e importe.")
                return
            try:
                if cost is None:
                    self.cost_service.create_cost(name=name_var.get(), amount=amount, cost_type=cost_type)
                else:
                    self.cost_service.update_cost(cost.id, name=name_var.get(), amount=amount)
                modal.destroy()
                self.refresh_costs(cost_type)
                self.refresh_products()
                self.refresh_stats()
            except Exception as error:
                messagebox.showerror("Costes", str(error))

        footer = tk.Frame(modal.body, bg=PANEL_ALT)
        footer.pack(fill="x", pady=(22, 0))
        HoverButton(footer, text="Cancelar", command=modal.destroy, bg=SHELL, hover_bg=ACCENT_SOFT, active_bg=ACCENT_SOFT, fg=TEXT, font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="right", padx=6)
        HoverButton(footer, text="Guardar", command=submit, bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="right", padx=6)

    def open_product_filter_modal(self) -> None:
        modal = BaseModal(self, "Filtrar productos", "420x320")
        name_var = tk.StringVar(value=self.product_filters["name"])
        min_var = tk.StringVar(value=self.product_filters["min_sale_price"])
        max_var = tk.StringVar(value=self.product_filters["max_sale_price"])
        for label, variable in (("Nombre", name_var), ("Precio minimo", min_var), ("Precio maximo", max_var)):
            tk.Entry(modal.field(label), textvariable=variable, font=("Segoe UI", 12), relief="flat", bd=0, bg=SHELL, fg=TEXT).pack(fill="x", pady=(6, 0), ipady=10)

        def apply_filters() -> None:
            self.product_filters = {"name": name_var.get(), "min_sale_price": min_var.get(), "max_sale_price": max_var.get()}
            modal.destroy()
            self.refresh_products()

        footer = tk.Frame(modal.body, bg=PANEL_ALT)
        footer.pack(fill="x", pady=(22, 0))
        HoverButton(footer, text="Aplicar", command=apply_filters, bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="right", padx=6)

    def open_cost_filter_modal(self, cost_type: str) -> None:
        modal = BaseModal(self, "Filtrar costes", "420x220")
        filters = self.variable_filters if cost_type == "variable" else self.fixed_filters
        name_var = tk.StringVar(value=filters["name"])
        tk.Entry(modal.field("Nombre"), textvariable=name_var, font=("Segoe UI", 12), relief="flat", bd=0, bg=SHELL, fg=TEXT).pack(fill="x", pady=(6, 0), ipady=10)

        def apply_filters() -> None:
            if cost_type == "variable":
                self.variable_filters["name"] = name_var.get()
            else:
                self.fixed_filters["name"] = name_var.get()
            modal.destroy()
            self.refresh_costs(cost_type)

        footer = tk.Frame(modal.body, bg=PANEL_ALT)
        footer.pack(fill="x", pady=(22, 0))
        HoverButton(footer, text="Aplicar", command=apply_filters, bg=ACCENT, hover_bg=ACCENT_DEEP, active_bg=ACCENT_DEEP, fg="white", font=("Segoe UI", 11, "bold"), padx=18, pady=10, cursor="hand2").pack(side="right", padx=6)

    def delete_product(self, product: Product) -> None:
        if not messagebox.askyesno("Producto", f"Eliminar '{product.name}'?"):
            return
        try:
            self.product_service.delete_product(product.id)
            self.refresh_products()
        except Exception as error:
            messagebox.showerror("Producto", str(error))

    def delete_cost(self, cost: Cost, cost_type: str) -> None:
        if not messagebox.askyesno("Coste", f"Eliminar '{cost.name}'?"):
            return
        try:
            self.cost_service.delete_cost(cost.id)
            self.refresh_costs(cost_type)
            self.refresh_products()
            self.refresh_stats()
        except Exception as error:
            messagebox.showerror("Coste", str(error))

    def renew_fixed_cost(self, cost: Cost) -> None:
        try:
            self.cost_service.renew_fixed_cost(cost.id)
            self.refresh_costs("fixed")
            self.refresh_stats()
        except Exception as error:
            messagebox.showerror("Coste fijo", str(error))


if __name__ == "__main__":
    app = OdinDesktopApp()
    app.mainloop()
