import os
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from queue import add_task

app = FastAPI()

# ---------------- TELEGRAM APP ----------------
application = ApplicationBuilder().token(BOT_TOKEN).build()

user_links = {}

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 V4 ULTRA PRO Bot is LIVE\nSend a link!")

# ---------------- HANDLE LINK ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.message.from_user.id

    if not url.startswith("http"):
        await update.message.reply_text("❌ Invalid link")
        return

    user_links[user_id] = url

    keyboard = [
        [
            InlineKeyboardButton("720p", callback_data="720"),
            InlineKeyboardButton("360p", callback_data="360"),
        ],
        [InlineKeyboardButton("BEST", callback_data="best")],
    ]

    await update.message.reply_text(
        "Choose quality:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ---------------- BUTTON ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    quality = query.data
    url = user_links.get(user_id)

    if not url:
        await query.edit_message_text("Session expired")
        return

    await query.edit_message_text("⏳ Processing...")

    add_task(user_id, url, quality, application, query.message.chat_id)

# ---------------- REGISTER HANDLERS ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(CallbackQueryHandler(button))


# ---------------- FASTAPI WEBHOOK ----------------
@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.start()
    print("🤖 Bot initialized")


@app.on_event("shutdown")
async def shutdown():
    await application.stop()


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


# ---------------- HEALTH CHECK ----------------
@app.get("/")
def home():
    return {"status": "V4 ULTRA PRO RUNNING 🚀"}