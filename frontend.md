# Odin API — Frontend Guide

This document defines how to interact with the Odin backend.

👉 IMPORTANT:
- Do NOT modify backend code
- Use only HTTP requests
- All communication is JSON-based
- Base URL: http://127.0.0.1:8000

---

## 🧪 Health Check

### GET /api/health

Check if backend is running.

Response:
```json
{ "status": "ok" }
````

---

# 📦 PRODUCTS

### GET /api/products

Get all products

---

### POST /api/products

Create a new product

Body:

```json
{
  "name": "Burger",
  "sale_price": 10,
  "variable_cost_ids": [1, 2]
}
```

---

### GET /api/products/{id}

Get product by id

---

### PATCH /api/products/{id}

Update product

---

### DELETE /api/products/{id}

Delete product

---

### GET /api/products/{id}/costs

Get costs assigned to a product

---

### POST /api/products/{id}/costs

Assign cost to product

Body:

```json
{
  "cost_id": 1
}
```

---

### DELETE /api/products/{id}/costs/{cost_id}

Remove cost from product

---

# 💸 COSTS

### GET /api/costs

Get all costs

---

### POST /api/costs

Create cost

Body:

```json
{
  "name": "Cheese",
  "amount": 2,
  "cost_type": "variable"
}
```

---

### GET /api/costs/{id}

Get cost by id

---

### PATCH /api/costs/{id}

Update cost

---

### DELETE /api/costs/{id}

Delete cost

---

# 📊 PRICING

### GET /api/pricing/margin?minimum_revenue=5000

Calculate margin based on minimum revenue

---

### POST /api/pricing/recommendations

Get pricing recommendations

---

### POST /api/pricing/products/{id}/recommendation

Get recommendation for a specific product

---

# 🛒 SALES

### GET /api/sales

Get all sales

---

### POST /api/sales

Create sale

---

### GET /api/sales/{id}

Get sale by id

---

### PATCH /api/sales/{id}

Update sale

---

### DELETE /api/sales/{id}

Delete sale

---

# 📈 STATS

### GET /api/stats/monthly

Monthly stats

---

### GET /api/stats/series

Time series data

---

# FILE STRUCTURE (Backend)

Each module handles its own endpoints:

* api/products_api.py
* api/costs_api.py
* api/pricing_api.py
* api/sales_api.py
* api/stats_api.py

---

# RULES

* Always send JSON in POST/PATCH
* Always expect JSON responses
* Do not assume hidden fields
* Use IDs from responses
* Handle errors (status != 200)

---

# WORKFLOW EXAMPLE

1. Create cost
2. Create product
3. Assign costs to product
4. Create sales
5. Request stats or pricing

---

# FRONTEND TIP

Example request:

```js
fetch("http://127.0.0.1:8000/api/products")
  .then(res => res.json())
  .then(data => console.log(data));
```

---

This API is the single source of truth.
Frontend should only communicate through these endpoints.

```

