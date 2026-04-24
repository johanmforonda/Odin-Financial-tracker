# Odin

**Odin** is a financial decision system designed for small businesses to calculate **minimum viable pricing** based on real cost structures.

The system helps answer a key business question:

> Is this product financially sustainable?

---

## Overview

Odin provides a structured way to:

- Track products, costs, and sales
- Understand cost structure
- Calculate sustainable pricing
- Analyze profitability

It is built as a **modular backend system** with multiple interfaces:
- CLI (command-line interface)
- HTTP API (for frontend integration)

---

## Architecture

The project follows a layered architecture:

```

core/        → Domain logic and business rules
data/        → Persistence (repositories + SQLite)
odin_api/    → HTTP API layer (handlers + routing)
cli/         → Command-line interface
app/         → Application bootstrap

```

### Key Concepts

- Domain-driven structure (domain, services, models)
- Repository pattern for persistence
- Service layer for business logic
- Custom HTTP dispatcher (no external frameworks)

---

## Features

- Product management
- Fixed and variable cost tracking
- Sales tracking
- Pricing logic based on cost structure
- Financial statistics and analysis

---

## API

The backend exposes an HTTP API under:

```

[http://127.0.0.1:8000/api](http://127.0.0.1:8000/api)

````

## Running the API

```bash
python api.py
````

Then open:

```
http://127.0.0.1:8000/api/health
```

---

## CLI Interface

The project also includes a CLI interface:

```bash
python cli.py
```

This allows interacting with the system without a frontend.

---

## Frontend Integration

This backend is designed to be consumed by a frontend application.

Important:

* Do not interact directly with internal code
* Use only the `/api` endpoints
* All communication is JSON-based

---

## Design Decisions

* Backend-first approach
* Clear separation of concerns (domain, infrastructure, interface)
* Custom HTTP server instead of frameworks for full control
* API designed as a contract for external clients (e.g. frontend)

---

## Tech Stack

* Python
* SQLite
* Custom HTTP server (`BaseHTTPRequestHandler`)

---

## Current Status

* Functional backend system
* API ready for frontend integration
* CLI-based interface available
* Frontend under development

---

## Author

**Johan Andres Martinez Foronda**

* Backend development
* System design
* Business-oriented software

Note:
The frontend is being developed separately.
This repository focuses on backend architecture, business logic, and data handling.

---

## Disclaimer

This is an MVP intended for learning, iteration, and demonstration.
Not production-ready.

```