# Odin

Odin es un sistema de decision financiera para pequenos negocios. Incluye un CLI interactivo y ahora tambien una API HTTP para que otro frontend pueda consumir todas las features del sistema.

## Caracteristicas

- Gestion de productos
- Gestion de costes fijos y variables
- Asignacion de costes variables a productos
- Recomendacion de precios segun ingresos objetivo
- Registro y consulta de ventas
- Resumen financiero y evolucion de rentabilidad
- API HTTP para integracion con frontend externo

## Estructura

- `core/`: logica de dominio y servicios
- `data/`: SQLite, esquema y repositorios
- `odin_api/`: servidor HTTP y endpoints por servicio
- `app/`: composicion compartida y arranque de servicios
- `cli/ui.py`: helpers de presentacion y estetica del terminal
- `cli/app.py`: flujo interactivo y logica del CLI
- `api.py`: punto de entrada del servidor HTTP
- `cly.py`: punto de entrada del CLI
- `main.py`: alias de compatibilidad para levantar la API

## Ejecucion

CLI:

```bash
python cly.py
```

API:

```bash
python api.py
```
