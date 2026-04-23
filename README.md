# Odin

**Odin** is a financial decision system designed for small businesses (initially restaurants) to determine **minimum viable pricing** based on real cost structures.

The goal is simple:  
> Ensure that every product sold contributes to covering costs and sustaining the business.

---

## Overview

Odin helps answer a critical question:

> *Is this product financially sustainable?*

Instead of relying on intuition or competitor pricing, Odin uses:
- Real costs
- Historical sales constraints
- Break-even logic

to compute **data-driven pricing decisions**.

---

## Problem

Many small businesses:
- Do not track their real costs properly
- Set prices based on intuition or competitors
- Lack visibility over break-even thresholds

This often leads to:
- Hidden losses
- Unsustainable pricing
- Poor financial decisions

---

## Solution

Odin calculates the **minimum viable price** of a product using:

- Unit (variable) costs
- Fixed costs
- Minimum expected sales volume

This ensures:
> Each product contributes proportionally to covering total costs.

---

## Features

- 📦 Product management
- 💸 Fixed and variable cost tracking
- 📉 Minimum viable price calculation
- 📊 Basic financial dashboard
- 🔁 Sales tracking and impact on profitability

---

## Core Logic

Conceptually:

- Total Required Revenue = Fixed Costs + Variable Costs  
- Minimum Price = Total Required Revenue / Minimum Expected Sales  

Odin operationalizes this logic in a modular and extensible system.

---

## Tech Stack

- **Backend:** Python  
- **Frontend:** HTML / CSS / JavaScript  
- **Architecture:** Modular (domain + services + repositories)  
- **Storage:** SQLite  

---

## Architecture

The system is structured with clear separation of concerns:

- `core/` → Domain logic and business rules  
- `services/` → Application logic (pricing, costs, sales)  
- `data/` → Persistence layer (repositories, database)  
- `web/` → Frontend interface  
- `web_app.py` → HTTP server + API layer  

This structure allows:
- Easy extension
- Maintainable logic
- Real-world scalability

---

## ⚠️ Frontend Note

The frontend was generated with the assistance of AI tools.

Its purpose is **purely functional**:
- Provide a usable interface
- Allow interaction with the backend system

The core of the project — including:
- System design
- Business logic
- Backend architecture
- Data modeling
- Persistence layer

was fully designed and implemented manually.

---

## How to run

```bash
python web_app.py