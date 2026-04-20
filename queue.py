import asyncio
from downloader import download_video
from storage import send_to_user

queue = []
processing = False

def add_task(user_id, url, quality, app, chat_id):
    queue.append((user_id, url, quality, app, chat_id))
    asyncio.create_task(worker())

async def worker():
    global processing

    if processing:
        return

    processing = True

    while queue:
        user_id, url, quality, app, chat_id = queue.pop(0)

        try:
            file_path, title = download_video(url, quality)

            await send_to_user(app, chat_id, file_path, title)

        except Exception as e:
            await app.bot.send_message(chat_id, f"❌ Error: {str(e)}")

    processing = False