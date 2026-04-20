import os

async def send_to_user(app, chat_id, file_path, title):
    if not os.path.exists(file_path):
        await app.bot.send_message(chat_id, "❌ File not found")
        return

    with open(file_path, "rb") as f:
        await app.bot.send_video(chat_id, f, caption=title)

    os.remove(file_path)