import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.handlers import start, handle_message


def main() -> None:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("Не найден BOT_TOKEN в .env")

    logging.basicConfig(
        level=logging.INFO,
        format="[{levelname}] {asctime} {name}: {message}",
        style="{",
    )

    # Чтобы в логах не печатались URL с токеном
    logging.getLogger("httpx").setLevel(logging.WARNING)

    app = Application.builder().token(bot_token).build()

    # /start
    app.add_handler(CommandHandler("start", start))
    # обычные текстовые сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
