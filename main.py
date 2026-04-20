import os
import asyncio
import logging
import yt_dlp

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

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

app = FastAPI()
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ---------------- STORAGE ----------------
queue = asyncio.Queue()
user_data = {}

# ---------------- PLATFORM DETECTOR ----------------
def detect_platform(url: str):
    if "tiktok" in url:
        return "TikTok"
    elif "facebook" in url or "fb" in url:
        return "Facebook"
    elif "youtu" in url:
        return "YouTube"
    return "Unknown"


# ---------------- DOWNLOAD ENGINE ----------------
def download_video(url, quality):
    format_map = {
        "720": "best[height<=720]",
        "360": "best[height<=360]",
        "best": "best",
    }

    ydl_opts = {
        "format": format_map.get(quality, "best"),
        "outtmpl": "downloads/%(title).50s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
    }

    os.makedirs("downloads", exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

    return file_path


# ---------------- WORKER ----------------
async def worker():
    while True:
        user_id, chat_id, quality = await queue.get()

        url = user_data.get(user_id)

        if not url:
            queue.task_done()
            continue

        msg = await application.bot.send_message(
            chat_id=chat_id,
            text="⏳ Starting download..."
        )

        try:
            file_path = await asyncio.to_thread(
                download_video, url, quality
            )

            await msg.edit_text("📤 Uploading...")

            await application.bot.send_video(
                chat_id=chat_id,
                video=open(file_path, "rb"),
                caption=f"✅ Done ({detect_platform(url)}) - {quality}"
            )

            os.remove(file_path)

        except Exception as e:
            logging.error(e)
            await msg.edit_text("❌ Download failed")

        queue.task_done()


# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 V5 PRO DOWNLOADER\nSend me a video link"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.message.from_user.id

    if not url.startswith("http"):
        await update.message.reply_text("❌ Invalid link")
        return

    user_data[user_id] = url

    keyboard = [
        [
            InlineKeyboardButton("720p", callback_data="720"),
            InlineKeyboardButton("360p", callback_data="360"),
        ],
        [InlineKeyboardButton("BEST", callback_data="best")],
    ]

    await update.message.reply_text(
        "🎬 Choose quality:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat_id
    quality = query.data

    await queue.put((user_id, chat_id, quality))

    await query.edit_message_text("🟡 Added to queue...")


# ---------------- REGISTER HANDLERS ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(CallbackQueryHandler(button))


# ---------------- FASTAPI ----------------
@app.get("/")
def home():
    return {"status": "V5 PRO RUNNING 🚀"}


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.start()

    asyncio.create_task(worker())

    if WEBHOOK_URL:
        await application.bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook set: {WEBHOOK_URL}")


@app.on_event("shutdown")
async def shutdown():
    await application.stop()
