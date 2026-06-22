# UCUSnack Inventory Bot 📦

A Telegram bot for managing snack inventory across dormitory wings at UCU (Ukrainian Catholic University).

## What It Does

The bot connects to the WooCommerce store at `ucusnack.com` via REST API and a custom inventory plugin, allowing you to:

- see **what needs to be restocked** in each dormitory wing (K1 / K2)
- get a breakdown **by product** — where and how much is needed
- check **warehouse stock** — the difference between the total WooCommerce quantity and the sum across all wings
- **update stock quantities** at a specific wing directly from Telegram

## Commands / Buttons

| Button | Action |
|---|---|
| 📦 By wings K1 | What needs to be delivered to each K1 wing |
| 📦 By wings K2 | What needs to be delivered to each K2 wing |
| 📋 By products K1 | Same data, grouped by product |
| 📋 By products K2 | Same data, grouped by product |
| 🏭 Warehouse stock | Current warehouse inventory |
| ✏️ Update quantity | Update stock at a specific wing |

## Setup & Running

### 1. Install dependencies

```bash
pip install python-telegram-bot requests
```

### 2. Set environment variables

```bash
export TELEGRAM_TOKEN="your_token_from_BotFather"
export WC_KEY="ck_..."
export WC_SECRET="cs_..."
```

### 3. Run

```bash
python tg_bot.py
```

## Locations

The bot covers **15 locations** across two buildings:

- **K1** — 8 dormitory wings
- **K2** — 6 dormitory wings
- **Студпростір** — a separate point with a limited product selection

## How Warehouse Stock Is Calculated

```
Warehouse stock = Total stock_quantity in WooCommerce − Sum across all wings
```

## Updating Inventory

When prompted, send a list in this format:

```
• Milka Oreo — 3 pcs.
• Snickers — 5 pcs.
```

The bot will ask you to select a wing, then accept the list and update the data via the API.
