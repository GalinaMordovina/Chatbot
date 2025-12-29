import re

import validators
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import ContextTypes

from bot.media_fetcher import fetch_tweet, cleanup_result


# Регулярка: поддерживаем twitter.com и x.com
TWITTER_RE = re.compile(
    r"(https?://(www\.)?(twitter\.com|x\.com)/\S+/status/\S+)",
    re.IGNORECASE
)


def extract_twitter_url(text: str) -> str | None:
    """Пытаемся вытащить из текста валидную ссылку на твит."""
    if not text:
        return None

    m = TWITTER_RE.search(text)
    if not m:
        return None

    url = m.group(1)
    return url if validators.url(url) else None


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start."""
    await update.message.reply_text(
        "Привет!\n\n"
        "Кинь ссылку на твит (x.com / twitter.com) \n"
        "я пришлю текст и медиа (фото/видео), чтобы можно было пересылать дальше."
    )


async def handle_message(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатываем обычные сообщения пользователя (ссылки)."""
    url = extract_twitter_url(update.message.text or "")
    if not url:
        await update.message.reply_text(
            "Пришли ссылку на твит вида:\n"
            "https://x.com/<user>/status/<id>"
        )
        return

    await update.message.reply_text("⏳ Достаю твит...")

    res = None
    try:
        # Скачиваем и вытаскиваем данные
        res = fetch_tweet(url)

        # Кнопка на оригинальный твит
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Открыть твит", url=res.url)]]
        )

        # Собираем красивую подпись
        head = " <b>Twitter/X</b>"
        by = f"\n👤 <i>{res.author}</i>" if res.author else ""
        body = f"\n\n{res.text}" if res.text else ""
        caption = f"{head}{by}{body}\n\n🔗 {res.url}"

        # Если медиа нет просто текст + ссылка
        if not res.items:
            await update.message.reply_text(
                caption,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=False,
            )
            return

        # Если одно медиа отправляем как фото/видео
        if len(res.items) == 1:
            item = res.items[0]
            if item.is_video:
                with open(item.file_path, "rb") as f:
                    await update.message.reply_video(
                        video=f,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
            else:
                with open(item.file_path, "rb") as f:
                    await update.message.reply_photo(
                        photo=f,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
            return

        # Если медиа много отправляем альбом (до 10 элементов)
        media_group = []
        file_handles = []

        try:
            for idx, item in enumerate(res.items[:10]):
                fh = open(item.file_path, "rb")
                file_handles.append(fh)

                if item.is_video:
                    media_group.append(
                        InputMediaVideo(
                            media=fh,
                            caption=caption if idx == 0 else None,
                            parse_mode="HTML" if idx == 0 else None,
                        )
                    )
                else:
                    media_group.append(
                        InputMediaPhoto(
                            media=fh,
                            caption=caption if idx == 0 else None,
                            parse_mode="HTML" if idx == 0 else None,
                        )
                    )

            await update.message.reply_media_group(media=media_group)
            await update.message.reply_text("🔗 Открыть оригинал:", reply_markup=keyboard)

        finally:
            # Очень важно закрывать файловые дескрипторы на Windows
            for fh in file_handles:
                try:
                    fh.close()
                except Exception:
                    pass

    except Exception as e:
        await update.message.reply_text(f"Не удалось обработать твит: {type(e).__name__}: {e}")

    finally:
        # Всегда чистим временную папку
        if res is not None:
            cleanup_result(res)
