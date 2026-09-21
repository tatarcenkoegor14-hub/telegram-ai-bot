import os
from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from huggingface_hub import InferenceClient


# =========================
# НАСТРОЙКИ
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

CHAT_MODEL = "openai/gpt-oss-120b"
VOICE_MODEL = "openai/whisper-large-v3"


# Проверяем наличие токенов
if not TELEGRAM_TOKEN:
    raise ValueError(
        "Не найден TELEGRAM_TOKEN. "
        "Добавь его в переменные окружения."
    )

if not HF_TOKEN:
    raise ValueError(
        "Не найден HF_TOKEN. "
        "Добавь его в переменные окружения."
    )


client = InferenceClient(
    api_key=HF_TOKEN
)


# =========================
# КОМАНДА /start
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я твой AI-помощник.\n\n"
        "💬 Отвечаю на сообщения\n"
        "🎙️ Распознаю голосовые сообщения\n"
        "🇺🇦 Поддерживаю украинский язык\n"
        "🇷🇺 Поддерживаю русский язык"
    )


# =========================
# AI
# =========================

def ask_ai(question):

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты дружелюбный AI-помощник. "
                    "Отвечай понятно и кратко. "
                    "Определи язык сообщения пользователя "
                    "и отвечай на том же языке. "
                    "Если пользователь пишет на украинском — "
                    "отвечай на украинском. "
                    "Если пользователь пишет на русском — "
                    "отвечай на русском. "
                    "Если пользователь пишет на английском — "
                    "отвечай на английском."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ],
        max_tokens=500
    )

    return response.choices[0].message.content


# =========================
# ТЕКСТОВЫЕ СООБЩЕНИЯ
# =========================

async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        question = update.message.text

        print("Пользователь:", question)

        answer = ask_ai(question)

        await update.message.reply_text(
            answer
        )

    except Exception as e:

        print(
            "Ошибка AI:",
            repr(e)
        )

        await update.message.reply_text(
            "❌ Произошла ошибка при обращении к AI."
        )


# =========================
# ГОЛОСОВЫЕ СООБЩЕНИЯ
# =========================

async def voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        await update.message.reply_text(
            "🎙️ Слушаю..."
        )

        voice = update.message.voice

        telegram_file = await context.bot.get_file(
            voice.file_id
        )

        audio_data = await telegram_file.download_as_bytearray()

        result = client.automatic_speech_recognition(
            audio=bytes(audio_data),
            model=VOICE_MODEL
        )

        recognized_text = result.text

        print(
            "Распознано:",
            recognized_text
        )

        await update.message.reply_text(
            "📝 Я услышал:\n\n"
            + recognized_text
        )

        answer = ask_ai(
            recognized_text
        )

        await update.message.reply_text(
            answer
        )

    except Exception as e:

        print(
            "Ошибка голоса:",
            repr(e)
        )

        await update.message.reply_text(
            "❌ Не получилось распознать голос."
        )


# =========================
# ЗАПУСК
# =========================

def main():

    app = Application.builder().token(
        TELEGRAM_TOKEN
    ).build()

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Голос
    app.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_message
        )
    )

    # Текст
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message
        )
    )

    print(
        "🤖 AI-помощник запущен!"
    )

    print(
        "🇺🇦 Українська мова: OK"
    )

    print(
        "🇷🇺 Русский язык: OK"
    )

    print(
        "🎙️ Голос: OK"
    )

    app.run_polling()


# =========================
# START
# =========================

if __name__ == "__main__":
    main()
    if not HF_TOKEN:
        raise ValueError(
            "Не найден HF_TOKEN"
        )

    app = Application.builder().token(
        TELEGRAM_TOKEN
    ).build()

    # Команда /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Голосовые сообщения
    app.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_message
        )
    )

    # Обычный текст
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message
        )
    )

    print(
        "🤖 AI-помощник запущен!"
    )

    # Постоянная работа бота
    app.run_polling()


# =========================
# START
# =========================

if __name__ == "__main__":
    main()