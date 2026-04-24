from __future__ import annotations

from dataclasses import asdict, is_dataclass
from decimal import Decimal
from shutil import get_terminal_size
from textwrap import shorten


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def terminal_width() -> int:
    return max(80, min(get_terminal_size((100, 30)).columns, 120))


def separator(char: str = "-") -> str:
    return char * terminal_width()


def title(text: str, subtitle: str | None = None) -> str:
    lines = [separator("="), text.center(terminal_width()), separator("=")]
    if subtitle:
        lines.append(subtitle)
        lines.append(separator())
    return "\n".join(lines)


def section(text: str) -> str:
    return f"\n{text}\n{separator()}"


def menu(title_text: str, options: list[tuple[str, str]]) -> str:
    lines = [section(title_text)]
    lines.extend(f"[{key}] {label}" for key, label in options)
    return "\n".join(lines)


def panel(title_text: str, lines: list[str]) -> str:
    body = "\n".join(lines) if lines else "Sin datos."
    return f"{section(title_text)}\n{body}"


def info(message: str) -> str:
    return f"\n> {message}"


def success(message: str) -> str:
    return f"\nOK: {message}"


def error(message: str) -> str:
    return f"\nERROR: {message}"


def prompt(label: str) -> str:
    return f"{label}: "


def format_money(value: Decimal | int | float | str | None) -> str:
    if value is None:
        return "-"
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    formatted = f"{decimal_value:,.2f}"
    return f"EUR {formatted}"


def format_percent(value: Decimal | int | float | str | None) -> str:
    if value is None:
        return "-"
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    return f"{decimal_value:.2f}%"


def format_value(value: object) -> str:
    if isinstance(value, Decimal):
        return format_money(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    if value is None or value == "":
        return "-"
    if is_dataclass(value):
        return ", ".join(
            f"{key}={format_value(item)}" for key, item in asdict(value).items()
        )
    if isinstance(value, list):
        return str(len(value))
    return str(value)


def table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return "Sin registros."

    string_rows = [[format_value(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in string_rows:
        for index, cell in enumerate(row):
            widths[index] = min(max(widths[index], len(cell)), 32)

    def normalize(cell: str, width: int) -> str:
        if width <= 3:
            value = cell[:width]
        else:
            value = shorten(cell, width=width, placeholder="...")
        return value.ljust(width)

    header_line = " | ".join(normalize(header, widths[index]) for index, header in enumerate(headers))
    divider = "-+-".join("-" * width for width in widths)
    body = [
        " | ".join(normalize(cell, widths[index]) for index, cell in enumerate(row))
        for row in string_rows
    ]
    return "\n".join([header_line, divider, *body])


def key_value(items: list[tuple[str, object]]) -> str:
    label_width = max((len(label) for label, _ in items), default=0)
    return "\n".join(
        f"{label.ljust(label_width)} : {format_value(value)}" for label, value in items
    )
