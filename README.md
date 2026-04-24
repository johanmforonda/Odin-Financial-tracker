# Odin

Odin es un sistema backend para gestionar productos, costes, ventas, precios recomendados y estadisticas de rentabilidad.

## Estructura

- `backend/core/`: dominio, modelos y servicios
- `backend/data/`: SQLite, esquema y repositorios
- `backend/odin_api/`: servidor HTTP y endpoints
- `backend/cli/`: interfaz de linea de comandos
- `backend/app/`: bootstrap compartido de servicios
- `frontend/`: espacio para el frontend

## Arranque

API:

```bash
python api.py
```

CLI:

```bash
python cly.py
```

Compatibilidad:

```bash
python main.py
```

## API

La API expone rutas bajo `http://127.0.0.1:8000/api`.

Endpoint de salud:

```text
GET /api/health
```
