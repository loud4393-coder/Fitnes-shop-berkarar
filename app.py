import html
import json
import os
import re
import secrets
import time
from decimal import Decimal, InvalidOperation

import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 24 * 1024

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()

# Demo catalog is intentionally duplicated on the server. The browser never
# decides prices or totals; the server calculates them from this allow-list.
PRODUCTS = {
    "fs-shoe-01": {"name": "Velocity Runner", "category": "Кроссовки", "price": Decimal("1850.00")},
    "fs-shirt-01": {"name": "Onyx Training Tee", "category": "Футболки", "price": Decimal("690.00")},
    "fs-bag-01": {"name": "Aero Gym Duffel", "category": "Сумки", "price": Decimal("1250.00")},
    "fs-shorts-01": {"name": "Core Training Shorts", "category": "Шорты", "price": Decimal("540.00")},
    "fs-pants-01": {"name": "Flex Tapered Joggers", "category": "Штаны", "price": Decimal("980.00")},
    "fs-shirt-02": {"name": "Performance Compression Tee", "category": "Футболки", "price": Decimal("760.00")},
    "fs-bag-02": {"name": "Transit Crossbody", "category": "Сумки", "price": Decimal("820.00")},
    "fs-accessory-01": {"name": "Training Essentials Set", "category": "Аксессуары", "price": Decimal("430.00")},
}

# Best-effort cooldown for a small private demo. Serverless instances may not
# share memory, so this is not a substitute for a production rate limiter.
_recent_requests = {}


def clean(value, limit=180):
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def money(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".").replace(",", " ")


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "fitness-shop-demo", "telegram_configured": bool(BOT_TOKEN and ADMIN_ID)})


@app.post("/api/demo-order")
def demo_order():
    if not BOT_TOKEN or not ADMIN_ID:
        return jsonify({"error": "Демо-заказы пока не подключены. Попробуйте позже."}), 503

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Некорректный запрос."}), 400

    # Quiet bot-field honeypot. Real visitors should never fill this field.
    if clean(payload.get("website"), 120):
        return jsonify({"ok": True, "message": "Заявка принята."})

    remote = request.headers.get("x-forwarded-for", request.remote_addr or "unknown").split(",")[0].strip()
    now = time.time()
    if now - _recent_requests.get(remote, 0) < 12:
        return jsonify({"error": "Подождите немного перед следующим тестовым заказом."}), 429

    customer = clean(payload.get("name"), 80)
    phone = clean(payload.get("phone"), 40)
    city = clean(payload.get("city"), 80)
    method = clean(payload.get("method"), 20)
    address = clean(payload.get("address"), 180)
    comment = clean(payload.get("comment"), 300)
    consent = payload.get("consent") is True
    raw_items = payload.get("items")

    if not customer or not phone or not city:
        return jsonify({"error": "Заполните имя, телефон и город."}), 400
    if len(phone) < 6 or not re.search(r"\d", phone):
        return jsonify({"error": "Проверьте номер телефона."}), 400
    if method not in ("delivery", "pickup"):
        return jsonify({"error": "Выберите способ получения заказа."}), 400
    if method == "delivery" and not address:
        return jsonify({"error": "Укажите адрес доставки."}), 400
    if not consent:
        return jsonify({"error": "Подтвердите отправку данных для демонстрации."}), 400
    if not isinstance(raw_items, list) or not raw_items or len(raw_items) > 20:
        return jsonify({"error": "Корзина пуста или содержит слишком много позиций."}), 400

    order_lines = []
    total = Decimal("0.00")
    for item in raw_items:
        if not isinstance(item, dict):
            return jsonify({"error": "Некорректная позиция заказа."}), 400
        product_id = clean(item.get("id"), 40)
        product = PRODUCTS.get(product_id)
        try:
            quantity = int(item.get("quantity", 0))
        except (TypeError, ValueError):
            quantity = 0
        if not product or quantity < 1 or quantity > 10:
            return jsonify({"error": "Проверьте товары и их количество."}), 400
        line_total = product["price"] * quantity
        total += line_total
        order_lines.append((product, quantity, line_total))

    order_number = secrets.token_hex(3).upper()
    lines = [
        "<b>🏋️ FITNESS SHOP — ДЕМО-ЗАКАЗ</b>",
        f"<b>Заказ:</b> <code>FS-{order_number}</code>",
        "",
        f"<b>Покупатель:</b> {html.escape(customer)}",
        f"<b>Телефон:</b> <code>{html.escape(phone)}</code>",
        f"<b>Город:</b> {html.escape(city)}",
        f"<b>Получение:</b> {'Доставка' if method == 'delivery' else 'Самовывоз'}",
    ]
    if method == "delivery":
        lines.append(f"<b>Адрес:</b> {html.escape(address)}")
    lines.extend(["", "<b>Состав заказа:</b>"])
    for product, quantity, line_total in order_lines:
        lines.append(f"• {html.escape(product['name'])} × {quantity} — {money(line_total)} TMT")
    lines.extend(["", f"<b>Итого: {money(total)} TMT</b>"])
    if comment:
        lines.extend(["", f"<b>Комментарий:</b> {html.escape(comment)}"])
    lines.extend(["", "<i>Это демонстрационный заказ. Данные отправлены посетителем для показа работы системы.</i>"])

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_ID, "text": "\n".join(lines), "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=8,
        )
        response.raise_for_status()
        telegram_result = response.json()
        if not telegram_result.get("ok"):
            app.logger.error("Telegram rejected demo order: %s", telegram_result)
            return jsonify({"error": "Не удалось отправить заказ в Telegram. Попробуйте ещё раз."}), 502
    except (requests.RequestException, ValueError):
        app.logger.exception("Telegram delivery failed")
        return jsonify({"error": "Telegram временно не отвечает. Попробуйте ещё раз."}), 502

    _recent_requests[remote] = now
    return jsonify({"ok": True, "order_number": f"FS-{order_number}", "message": "Демонстрационный заказ отправлен."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
