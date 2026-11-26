# Fitness Shop — Demo Store

A standalone Flask + static frontend demo. Product data and image assets are local to the project. Demo orders are validated and forwarded to a dedicated Telegram bot; they are not saved to a database.

## Environment variables

- `BOT_TOKEN` — token of a dedicated demo bot created with `@BotFather`.
- `ADMIN_ID` — Telegram numeric user ID that receives demo orders.

Never commit `.env` or put the bot token in frontend JavaScript.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env      # then fill in real values
python app.py
```

Open `http://127.0.0.1:5000`.

## Vercel

Import this repository as a separate Vercel project, then add `BOT_TOKEN` and `ADMIN_ID` under Project Settings → Environment Variables and redeploy.

## Demo data notice

The checkout clearly tells visitors that the entered name, phone number, city, and (when delivery is selected) address are sent to the demo operator in Telegram. Use test contact details during presentations. This demo does not process payments or create real store orders.

## Before presenting

- Replace the temporary product artwork in `static/images/products/` with approved product photos.
- Confirm the store owner has authorized the use of their logo, brand assets, and product images.
- Test the complete checkout → Telegram → success flow after deploying.


Product images in this first pass are generated concept imagery, not proof of the shop's actual inventory or official Nike/Gymshark product photography. Replace them with store-approved product photos before presenting the demo as the shop's real catalog.


## Каталог и изображения

Демонстрационные товары, цены, категории, описания и фотографии находятся в `static/script.js`. Фотографии встроены в JavaScript как WebP data URI (Base64), поэтому папка `static/images/products/` для работы каталога не требуется.
