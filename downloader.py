import yt_dlp

def download_video(url, quality):
    ydl_opts = {
        "format": "best" if quality == "best" else f"best[height<={quality}]",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

    return file_path, info.get("title", "video")