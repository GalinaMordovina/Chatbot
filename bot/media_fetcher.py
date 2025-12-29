from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from yt_dlp import YoutubeDL

# Расширения файлов, которые будем считать видео
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}


@dataclass(frozen=True)
class MediaItem:
    """Один медиа-файл, скачанный из твита."""
    file_path: Path
    is_video: bool


@dataclass(frozen=True)
class FetchResult:
    """Результат “разбора” твита."""
    text: str               # текст твита (если доступен)
    author: str             # автор/канал (если доступно)
    url: str                # нормализованная ссылка на твит
    items: list[MediaItem]  # список медиа (фото/видео)
    work_dir: Path          # временная папка, где лежат скачанные файлы


def fetch_tweet(url: str) -> FetchResult:
    """
    Скачивает данные и медиа из Twitter/X через yt-dlp.

    Почему yt-dlp:
    - умеет вытаскивать медиа из многих сайтов
    - умеет раздельные видео/аудио потоки и склеивает их через ffmpeg
    """
    # Создаём временную папку, куда yt-dlp будет складывать файлы
    work_dir = Path(tempfile.mkdtemp(prefix="tg_tweet_"))

    # Шаблон имён файлов:
    # %(id)s id твита/видео
    # %(autonumber)s если несколько файлов (карусель), будут 1,2,3...
    outtmpl = str(work_dir / "%(id)s_%(autonumber)s.%(ext)s")

    # Опции yt-dlp
    ydl_opts: dict = {
        "outtmpl": outtmpl,
        "quiet": True,                # меньше шума в консоли
        "no_warnings": True,          # скрыть предупреждения
        "noplaylist": True,           # не пытаться качать плейлисты
        # берем видео+аудио и ограничиваем качество
        "format": "bv*[height<=720]+ba/best[height<=720]/best",
        "merge_output_format": "mp4",  # Склеиваем результат в mp4
    }

    # Достаём инфо и сразу скачиваем
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # Иногда yt-dlp возвращает “entries” (как список), тогда берём первый элемент
    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    # Текст твита чаще всего лежит в "description"
    text = (info.get("description") or "").strip()

    # Автор: чаще всего "uploader" или "uploader_id"
    author = (info.get("uploader") or info.get("uploader_id") or "").strip()

    # Нормализованный URL (если yt-dlp его дал)
    page_url = info.get("webpage_url") or url

    # Собираем список скачанных файлов
    items: list[MediaItem] = []

    # requested_downloads чтобы понять какие файлы скачались
    requested = info.get("requested_downloads") or []
    for r in requested:
        fp = r.get("filepath")
        if not fp:
            continue
        p = Path(fp)
        if p.exists() and p.is_file():
            items.append(MediaItem(file_path=p, is_video=p.suffix.lower() in VIDEO_EXTS))

    # Если requested_downloads пуст, делаем fallback (берём все файлы из work_dir)
    if not items:
        for p in sorted(work_dir.iterdir()):
            if p.is_file():
                items.append(MediaItem(file_path=p, is_video=p.suffix.lower() in VIDEO_EXTS))

    return FetchResult(
        text=text,
        author=author,
        url=page_url,
        items=items,
        work_dir=work_dir,
    )


def cleanup_result(res: FetchResult) -> None:
    """Удаляет временную папку со скачанными файлами."""
    shutil.rmtree(res.work_dir, ignore_errors=True)
