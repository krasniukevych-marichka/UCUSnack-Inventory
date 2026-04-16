import logging
import re
import requests
from dotenv import load_dotenv
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

load_dotenv()

# ──────────────────────────────────────────
#  НАЛАШТУВАННЯ
# ──────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
WP_USER = os.environ["WP_USER"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]

INVENTORY_URL = "https://ucusnack.com/wp-json/mulopimfwc/v1/inventory/export"
WC_PRODUCT_URL = "https://ucusnack.com/wp-json/wc/v3/products"
INVENTORY_UPDATE_URL = "https://ucusnack.com/wp-json/mulopimfwc/v1/inventory/update"

LOCATION_IDS = {
    "K1 крило Тригуб": 43,
    "К1 крило Волощак": 37,
    "К1 крило Гнилиці": 39,
    "К1 крило Журби": 41,
    "К1 крило Квасюків": 42,
    "К1 крило Куки": 40,
    "К1 крило Мисяковського": 38,
    "К1 крило Плетених": 35,
    "К2 крило Байковських": 44,
    "К2 крило Жолдак": 47,
    "К2 крило Мельників і Лучників": 45,
    "К2 крило Мельниченка": 48,
    "К2 крило Нагорних": 46,
    "К2 крило Федини": 34,
    "Студпростір": 49,
}

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
    "CHIPSTER'S хвилясті зі смаком \"Томат Спайсі\"": 1,
    'Coca Cola 0,33л': 4,
    'Fanta 0.33л': 2,
    'FUZE Tea "Лісові ягоди" 0,5л': 2,
    'FUZE Tea "Персик" 0,5л': 2,
    'KINDER Chocolate 4шт': 0,
    'KINDER Chocolate 8шт': 1,
    'MARS': 2,
    'MILKA Alpine milk (snack pack)': 0,
    'MILKA Hazelnut (snack pack)': 2,
    'Milka Strawberry': 1,
    'Milka Oreo': 1,
    'OREO cookies (6шт)' : 2,
    'OREO cookies (10шт)': 0,
    'PRINGLES original (маленькі)': 0,
    'PRINGLES зі смаком "Паприка"': 1,
    'PRINGLES зі смаком "Паприка" (маленькі)': 1,
    'PRINGLES зі смаком "Сир і цибуля"': 0,
    'PRINGLES зі смаком "Піца"': 0,
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
    'Локшина REEVA зі смаком Гриби': 2,
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

CHOOSING_LOCATION, WAITING_FOR_UPDATE = range(2)

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
        if loc_name == "Студпростір" and name in K2_EXCLUDED:
            continue  # цей товар не відносимо в студпростір

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


def get_product_id_map():
    """Повертає словник назва товару -> product_id."""
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
    return {item["product_name"].strip(): item["product_id"] for item in items}


def get_location_stock(product_id, location_id):
    """Отримує поточний stock товару на локації."""
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

    for item in items:
        if item["product_id"] == product_id and item["location_id"] == location_id:
            stock_raw = item.get("stock", "")
            try:
                return int(stock_raw) if stock_raw != "" else 0
            except (ValueError, TypeError):
                return 0
    return 0


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

def parse_update_message(text):
    """
    Парсить повідомлення формату:
    • Milka Oreo — 1 шт.
    • Coca Cola 0,33л — -2 шт.
    Повертає список (назва, кількість).
    """
    results = []
    lines = text.strip().split("\n")
    pattern = re.compile(r"[•\-]?\s*(.+?)\s*[—\-]+\s*(-?\d+)")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = pattern.search(line)
        if m:
            name = m.group(1).strip().rstrip("—").strip()
            qty = int(m.group(2))
            results.append((name, qty))
    return results

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
        [
            InlineKeyboardButton("✏️ Оновити кількість", callback_data="update_start"),
        ],
    ]
    await update.message.reply_text(
        "Привіт! Що хочеш подивитись?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def view_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in ("update_start", "cancel") or query.data.startswith("updloc_"):
        return
    
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
#  ХЕНДЛЕРИ — ОНОВЛЕННЯ КІЛЬКОСТІ
# ──────────────────────────────────────────
async def update_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton(loc, callback_data=f"updloc_{loc}")]
                for loc in sorted(LOCATION_IDS.keys())]
    keyboard.append([InlineKeyboardButton("❌ Скасувати", callback_data="cancel")])

    await query.edit_message_text(
        "Вибери крило для оновлення:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_LOCATION


async def location_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    location_name = query.data.replace("updloc_", "")
    context.user_data["update_location"] = location_name

    await query.edit_message_text(
        f"📍 *{location_name}*\n\n"
        f"Надішли список товарів у форматі:\n"
        f"```\n"
        f"• Milka Oreo — 1 шт.\n"
        f"• Coca Cola 0,33л — 3 шт.\n"
        f"• SNICKERS — -1 шт.\n"
        f"```\n"
        f"Або /cancel щоб скасувати.",
        parse_mode="Markdown"
    )
    return WAITING_FOR_UPDATE


async def process_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auth = (WP_USER, WP_APP_PASSWORD)
    location_name = context.user_data.get("update_location")
    location_id = LOCATION_IDS.get(location_name)

    if not location_id:
        await update.message.reply_text("❌ Помилка: локацію не знайдено.")
        return ConversationHandler.END

    text = update.message.text
    parsed = parse_update_message(text)

    if not parsed:
        await update.message.reply_text(
            "❌ Не вдалось розпізнати список. Перевір формат:\n"
            "• Назва товару — кількість шт."
        )
        return WAITING_FOR_UPDATE

    # Отримати product_id map
    await update.message.reply_text("⏳ Оновлюю...")
    product_id_map = get_product_id_map()

    results = []
    errors = []

    for name, qty in parsed:
        pid = product_id_map.get(name)
        if not pid:
            errors.append(f"❓ Товар не знайдено: *{name}*")
            continue

        try:
            # Отримати поточний stock на локації та загальний
            current_loc_stock = get_location_stock(pid, location_id)
            new_loc_stock = current_loc_stock + qty

            wc_resp = requests.get(f"{WC_PRODUCT_URL}/{pid}", auth=auth, timeout=15)
            current_wc = wc_resp.json().get("stock_quantity") or 0

            # Оновити крило (плагін зіпсує stock_quantity)
            requests.post(
                INVENTORY_UPDATE_URL,
                auth=auth,
                json={"product_id": pid, "location_id": location_id, "stock": new_loc_stock},
                timeout=15
            )

            # Виправити загальний stock залежно від знаку
            if qty > 0:
                # Товар перемістили зі складу на крило — загальний не змінюється
                new_wc = current_wc
            else:
                # Товар списали — загальний зменшується
                new_wc = current_wc + qty

            # Відразу виправити загальний stock
            requests.put(
                f"{WC_PRODUCT_URL}/{pid}",
                auth=auth,
                json={"stock_quantity": new_wc},
                timeout=15
            )

            sign = "+" if qty > 0 else ""
            results.append(f"✅ {name}: {sign}{qty} шт.")

        except Exception as e:
            errors.append(f"❌ Помилка для *{name}*: {e}")

    # Відповідь
    response = f"📍 *{location_name}*\n\n"
    if results:
        response += "\n".join(results)
    if errors:
        response += "\n\n" + "\n".join(errors)

    await update.message.reply_text(response, parse_mode="Markdown")

    # Показати меню знову
    keyboard = [
        [
            InlineKeyboardButton("📦 По крилах К1", callback_data="loc_k1"),
            InlineKeyboardButton("📦 По крилах К2", callback_data="loc_k2"),
        ],
        [
            InlineKeyboardButton("📋 По товарах К1", callback_data="prod_k1"),
            InlineKeyboardButton("📋 По товарах К2", callback_data="prod_k2"),
        ],
        [InlineKeyboardButton("🏭 Залишок на складі", callback_data="warehouse")],
        [InlineKeyboardButton("✏️ Оновити кількість", callback_data="update_start")],
    ]
    await update.message.reply_text(
        "Готово! Що далі?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.")
    return ConversationHandler.END


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Скасовано.")
    return ConversationHandler.END

# ──────────────────────────────────────────
#  ЗАПУСК
# ──────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(update_start, pattern="^update_start$")],
        states={
            CHOOSING_LOCATION: [
                CallbackQueryHandler(location_chosen, pattern="^updloc_"),
                CallbackQueryHandler(cancel_callback, pattern="^cancel$"),
            ],
            WAITING_FOR_UPDATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_update),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(view_handler))

    print("Бот запущено!")
    app.run_polling()