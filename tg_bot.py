import logging
import requests
from dotenv import load_dotenv
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

# ──────────────────────────────────────────
#  НАЛАШТУВАННЯ
# ──────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
WP_USER = os.environ["WP_USER"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]

INVENTORY_URL = "https://ucusnack.com/wp-json/mulopimfwc/v1/inventory/export"
WC_PRODUCT_URL = "https://ucusnack.com/wp-json/wc/v3/products"

K1_WINGS = {
    "K1 крило Тригуб",
    "К1 крило Волощак",
    "К1 крило Гнилиці",
    "К1 крило Журби",
    "К1 крило Квасюків",
    "К1 крило Куки",
    "К1 крило Мисяковського",
    "К1 крило Плетених",
}

K2_WINGS = {
    "К2 крило Байковських",
    "К2 крило Жолдак",
    "К2 крило Мельників і Лучників",
    "К2 крило Мельниченка",
    "К2 крило Нагорних",
    "К2 крило Федини",
    "Студпростір",
}

# Товари яких НЕ треба відносити в К2+Студпростір
K2_EXCLUDED = {
    'AXA Каша вівсяна з вершками та горіхами в карамелі',
    'AXA Каша вівсяна з полуницею',
    'Локшина REEVA зі смаком Курки',
    'Локшина REEVA зі смаком Сиру та зелені',
}

# ──────────────────────────────────────────
#  ЦІЛЬОВІ КІЛЬКОСТІ
# ──────────────────────────────────────────
TARGET_STOCK = {
    'AXA Батончик зі смаком йогурту та з полуницею': 1,
    'AXA Батончик "Wild berries"': 1,
    'AXA Каша вівсяна з вершками та горіхами в карамелі': 1,
    'AXA Каша вівсяна з полуницею': 1,
    'BRO Crackers із сиром': 1,
    'BUENO Kinder': 4,
    "CHIPSTER'S зі смаком Крабу": 1,
    "CHIPSTER'S зі смаком Сметана та цибуля": 1,
    "CHIPSTER'S хвилясті зі смаком \"Гриби з вершковим соусом\"": 1,
    "CHIPSTER'S зі смаком Бекону": 0,
    'Coca Cola 0,33л': 4,
    'Fanta 0.33л': 2,
    'FUZE Tea "Лісові ягоди" 0,5л': 2,
    'FUZE Tea "Персик" 0,5л': 2,
    'KINDER Chocolate 4шт': 2,
    'KINDER Chocolate 8шт': 1,
    'MARS': 2,
    'MILKA Alpine milk (snack pack)': 0,
    'MILKA Hazelnut (snack pack)': 2,
    'Milka Strawberry': 1,
    'Milka Oreo': 1,
    'OREO cookies': 2,
    'PRINGLES original (маленькі)': 1,
    'PRINGLES зі смаком "Паприка"': 1,
    'PRINGLES зі смаком "Паприка" (маленькі)': 1,
    'PRINGLES зі смаком "Сир і цибуля"': 0,
    'PRINGLES зі смаком "Піца"': 1,
    'PRINGLES зі смаком "BBQ" (маленькі)': 0,
    'PRINGLES зі смаком "Сметана і зелень"': 1,
    'PRINGLES зі смаком "Сметана і зелень" (маленькі)': 1,
    'SNICKERS': 2,
    'Sprite 0.33л': 2,
    'TABLERONE': 1,
    'TWIX': 2,
    'Арахіс BIGBOB зі смаком Гриби у вершковому соусі': 0,
    'БАРНІ з шоколадом': 0,
    'Сухарики FLINT "Сметана із зеленню"': 1,
    'Грінки FLINT "Томат Спайсі"': 1,
    'Локшина REEVA зі смаком Курки': 2,
    'Локшина REEVA зі смаком Сиру та зелені': 2,
    'Кукурудза BIGBOB зі смаком Сиру': 1,
    'Насіння соняшника Ласунчик': 0,
    'Соломка солона': 4,
    'Чипси яблучні': 1,
    'ТУК зі смаком "Сир"': 1,
    'Сухарики FLINT "Бекон" (маленькі)': 1,
    'Сухарики FLINT "Краб" (маленькі)': 1,
    'BOB SNAIL Яблуко-груша-лимон мармелад': 0,
    'BOB SNAIL Яблуко-вишня мармелад': 0,
    'BOB SNAIL Яблучно-грушеві цукерки': 0,
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────
#  ОТРИМАННЯ ДАНИХ
# ──────────────────────────────────────────
def fetch_inventory():
    auth = (WP_USER, WP_APP_PASSWORD)
    items = []
    page = 1
    while True:
        resp = requests.get(INVENTORY_URL, auth=auth, params={"page": page}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        items.extend(payload.get("data", []))
        if not payload.get("has_more"):
            break
        page += 1

    # location_map: крило -> {товар: потрібно донести}
    # product_info: product_id -> {name, wings_total}
    location_map = {}
    product_info = {}

    for item in items:
        pid = item.get("product_id")
        name = item.get("product_name", "").strip()
        loc_name = item.get("location_name", "").strip()
        stock_raw = item.get("stock", "")

        try:
            current = int(stock_raw) if stock_raw != "" else 0
        except (ValueError, TypeError):
            current = 0

        if pid not in product_info:
            product_info[pid] = {"name": name, "wings_total": 0}
        product_info[pid]["wings_total"] += current

        # Визначаємо target залежно від групи крила
        if loc_name in K2_WINGS and name in K2_EXCLUDED:
            continue  # цей товар не відносимо в К2

        target = TARGET_STOCK.get(name, 0)
        needed = max(0, target - current)
        if needed > 0:
            location_map.setdefault(loc_name, {})[name] = needed

    # Склад = WC stock_quantity - сума по всіх крилах
    warehouse_stock = {}
    for pid, info in product_info.items():
        try:
            r = requests.get(f"{WC_PRODUCT_URL}/{pid}", auth=auth, timeout=15)
            wc_total = r.json().get("stock_quantity") or 0
            warehouse_stock[info["name"]] = wc_total - info["wings_total"]
        except Exception:
            warehouse_stock[info["name"]] = 0

    return location_map, warehouse_stock


def get_group_location_map(location_map, group):
    """Фільтрує location_map по групі (k1 або k2)."""
    wings = K1_WINGS if group == "k1" else K2_WINGS
    return {loc: products for loc, products in location_map.items() if loc in wings}


# ──────────────────────────────────────────
#  ФОРМАТУВАННЯ
# ──────────────────────────────────────────
def format_by_location(location_map):
    if not location_map:
        return "✅ Всі крила укомплектовані!"

    # Загальна сума по всіх крилах групи
    totals = {}
    for products in location_map.values():
        for name, cnt in products.items():
            totals[name] = totals.get(name, 0) + cnt

    lines = ["*ПОТРІБНО ДОНЕСТИ:*", "=" * 40]
    for product in sorted(totals):
        lines.append(f"{product} — {totals[product]} шт.")
    lines.append("")

    # Детально по крилах
    for location in sorted(location_map):
        lines.append(f"🏢 *{location}*")
        for product, count in location_map[location].items():
            lines.append(f"  • {product} — {count} шт.")
        lines.append("")
    return "\n".join(lines)


def format_by_product(location_map):
    if not location_map:
        return "✅ Нічого не треба поповнювати!"
    product_map = {}
    for location, products in location_map.items():
        for p_name, count in products.items():
            product_map.setdefault(p_name, []).append((location, count))
    lines = []
    for product in sorted(product_map):
        lines.append(f"🍫 *{product}*")
        for loc, cnt in sorted(product_map[product]):
            lines.append(f"  • {loc}: {cnt} шт.")
        lines.append("")
    return "\n".join(lines)


def format_warehouse(warehouse_stock):
    if not warehouse_stock:
        return "Склад порожній або дані недоступні."
    lines = ["🏭 *Залишок на складі:*\n"]
    for product, cnt in sorted(warehouse_stock.items()):
        emoji = "⚠️" if cnt <= 0 else "✅"
        lines.append(f"{emoji} {product} — {cnt} шт.")
    return "\n".join(lines)


def split_text(text, max_len=4000):
    lines = text.split("\n")
    chunk, chunks, length = [], [], 0
    for line in lines:
        if length + len(line) + 1 > max_len:
            chunks.append("\n".join(chunk))
            chunk, length = [], 0
        chunk.append(line)
        length += len(line) + 1
    if chunk:
        chunks.append("\n".join(chunk))
    return chunks


# ──────────────────────────────────────────
#  ХЕНДЛЕРИ
# ──────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📦 По крилах К1",    callback_data="loc_k1"),
            InlineKeyboardButton("📦 По крилах К2",    callback_data="loc_k2"),
        ],
        [
            InlineKeyboardButton("📋 По товарах К1",   callback_data="prod_k1"),
            InlineKeyboardButton("📋 По товарах К2",   callback_data="prod_k2"),
        ],
        [
            InlineKeyboardButton("🏭 Залишок на складі", callback_data="warehouse"),
        ],
    ]
    await update.message.reply_text(
        "Привіт! Що хочеш подивитись?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Збираю дані...")

    try:
        location_map, warehouse_stock = fetch_inventory()

        if query.data == "loc_k1":
            filtered = get_group_location_map(location_map, "k1")
            header = "📦 *По крилах К1:*\n"
            text = header + format_by_location(filtered)

        elif query.data == "loc_k2":
            filtered = get_group_location_map(location_map, "k2")
            header = "📦 *По крилах К2 + Студпростір:*\n"
            text = header + format_by_location(filtered)

        elif query.data == "prod_k1":
            filtered = get_group_location_map(location_map, "k1")
            header = "📋 *По товарах К1:*\n"
            text = header + format_by_product(filtered)

        elif query.data == "prod_k2":
            filtered = get_group_location_map(location_map, "k2")
            header = "📋 *По товарах К2 + Студпростір:*\n"
            text = header + format_by_product(filtered)

        elif query.data == "warehouse":
            text = format_warehouse(warehouse_stock)

        else:
            text = "Невідома команда."

        for chunk in split_text(text):
            await query.message.reply_text(chunk, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Помилка API")
        await query.message.reply_text(f"❌ Помилка: {e}")


# ──────────────────────────────────────────
#  ЗАПУСК
# ──────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Бот запущено!")
    app.run_polling()