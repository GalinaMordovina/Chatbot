# Twitter/X Media Telegram Bot

Телеграм-бот, который принимает ссылку на твит (x.com / twitter.com) и возвращает:
- текст поста
- медиа (фото/видео), включая несколько файлов (альбом до 10)
- аккуратную подпись + кнопку «Открыть твит»

## Возможности
- Поддержка ссылок на твиты: `https://x.com/<user>/status/<id>` и `https://twitter.com/<user>/status/<id>`
- Скачивание видео **со звуком** (через `yt-dlp` + `ffmpeg`)
- Отправка:
  - одного файла (photo/video) с подписью и кнопкой
  - либо альбома (media group), если медиа несколько

## Стек
- `Python 3.12+`
- `python-telegram-bot`
- `yt-dlp`
- `ffmpeg`

## Установка и запуск

### 1) Клонировать проект
```bash
git clone <repo_url>
cd Chatbot
```

### 2) Создать и активировать виртуальное окружение
Windows (PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
### 3) Установить зависимости
`python -m pip install -r requirements.txt

### 4)Установить ffmpeg
Самый простой способ на Windows:
`winget install Gyan.FFmpeg`
### 5) Создать .env
Создай файл .env в корне проекта:
`BOT_TOKEN=ваш_токен_бота`
Токен получить у @BotFather в Telegram.

###6) Запуск
`python main.py`
