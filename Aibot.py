import os
import asyncio

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================
# ЗАГРУЗКА ПЕРЕМЕННЫХ
# =========================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

CHAT_MODEL = "openai/gpt-oss-120b"
VOICE_MODEL = "openai/whisper-large-v3"


# =========================
# ПРОВЕРКА ТОКЕНОВ
# =========================

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


# =========================
# HUGGING FACE
# =========================

client = InferenceClient(
    api_key=HF_TOKEN
)


# =========================
# УКРАИНСКАЯ КЛАВИАТУРА
# =========================

keyboard = [
    ["💬 Поставити запитання"],
    ["🎙️ Голосовий помічник"],
    ["🌐 Мова"],
    ["ℹ️ Про бота"],
]

reply_keyboard = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True
)


# =========================
# /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🇺🇦 Вітаю! Я твій AI-помічник.\n\n"
        "🤖 Я можу:\n"
        "• відповідати на запитання;\n"
        "• спілкуватися різними мовами;\n"
        "• розпізнавати голосові повідомлення;\n"
        "• допомагати з навчанням та інформацією.\n\n"
        "🌍 Просто напиши мені повідомлення "
        "будь-якою мовою — я постараюся відповісти "
        "тією ж мовою.\n\n"
        "🎙️ Також можеш надіслати голосове повідомлення."
    )

    await update.message.reply_text(
        text,
        reply_markup=reply_keyboard
    )


# =========================
# AI
# =========================

async def ask_ai(question: str) -> str:

    try:

        messages = [
            {
                "role": "system",
                "content": (
                    "Ти дружелюбний багатомовний AI-помічник. "
                    "Відповідай зрозуміло, корисно та природно. "

                    "ВАЖЛИВО: визнач мову повідомлення користувача "
                    "та відповідай тією ж мовою. "

                    "Якщо користувач пише українською — відповідай "
                    "українською. "

                    "Якщо російською — російською. "

                    "Якщо англійською — англійською. "

                    "Якщо користувач використовує іншу мову, "
                    "намагайся відповідати цією ж мовою. "

                    "Не змінюй мову без причини. "
                    "Якщо користувач просить перекласти текст, "
                    "виконай його прохання."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ]

        response = client.chat_completion(
            messages=messages,
            model=CHAT_MODEL,
            max_tokens=1000,
            temperature=0.7
        )

        answer = response.choices[0].message.content

        if not answer:
            return "❌ AI не зміг сформувати відповідь."

        return answer

    except Exception as e:

        print("AI ERROR:", e)

        return (
            "❌ Сталася помилка під час звернення до AI.\n"
            "Спробуй ще раз через декілька секунд."
        )


# =========================
# ТЕКСТОВІ ПОВІДОМЛЕННЯ
# =========================

async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user_text = update.message.text

    # Кнопка запитання
    if user_text == "💬 Поставити запитання":

        await update.message.reply_text(
            "💬 Напиши своє запитання, і я спробую допомогти."
        )

        return

    # Кнопка голосового помічника
    if user_text == "🎙️ Голосовий помічник":

        await update.message.reply_text(
            "🎙️ Надішли мені голосове повідомлення.\n\n"
            "Я розпізнаю його та передам текст AI."
        )

        return

    # Кнопка мови
    if user_text == "🌐 Мова":

        await update.message.reply_text(
            "🌍 Мова визначається автоматично.\n\n"
            "Просто напиши мені українською, "
            "російською, англійською або іншою мовою — "
            "я постараюся відповісти тією ж мовою."
        )

        return

    # Кнопка про бота
    if user_text == "ℹ️ Про бота":

        await update.message.reply_text(
            "🤖 AI-помічник\n\n"
            "🇺🇦 Інтерфейс: українська\n"
            "🌍 Відповіді: багатомовні\n"
            "🎙️ Голос: підтримується\n"
            "🧠 AI: Hugging Face"
        )

        return

    # Показуємо, що бот думає
    await update.message.chat.send_action(
        action="typing"
    )

    answer = await ask_ai(user_text)

    await update.message.reply_text(answer)


# =========================
# ГОЛОСОВІ ПОВІДОМЛЕННЯ
# =========================

async def voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.voice:
        return

    try:

        await update.message.reply_text(
            "🎙️ Отримав голосове повідомлення.\n"
            "⏳ Розпізнаю..."
        )

        # Отримуємо файл Telegram
        voice_file = await update.message.voice.get_file()

        # Завантажуємо його в пам'ять
        audio_data = await voice_file.download_as_bytearray()

        # Розпізнаємо голос
        transcription = client.automatic_speech_recognition(
            audio=bytes(audio_data),
            model=VOICE_MODEL
        )

        # Отримуємо текст
        recognized_text = transcription.text

        if not recognized_text:

            await update.message.reply_text(
                "❌ Не вдалося розпізнати голос."
            )

            return

        await update.message.reply_text(
            f"📝 Я почув:\n\n{recognized_text}\n\n"
            "🤖 Думаю над відповіддю..."
        )

        # Передаємо розпізнаний текст AI
        answer = await ask_ai(recognized_text)

        await update.message.reply_text(answer)

    except Exception as e:

        print("VOICE ERROR:", e)

        await update.message.reply_text(
            "❌ Не вдалося обробити голосове повідомлення.\n"
            "Спробуй записати його ще раз."
        )


# =========================
# ЗАПУСК БОТА
# =========================

async def main():

    app = (
        Application
        .builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

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

    # Обычные текстовые сообщения
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message
        )
    )

    print("=================================")
    print("🤖 AI-помічник запущений!")
    print("🇺🇦 Український інтерфейс: OK")
    print("🌍 Багатомовний режим: OK")
    print("🎙️ Голосовий режим: OK")
    print("🚂 Railway mode: OK")
    print("=================================")

    # Запускаємо Telegram Application вручну.
    # Це обходить проблему Event loop is closed
    # на Railway.

    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    # Не дозволяємо програмі завершитися.
    await asyncio.Event().wait()


# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":
    asyncio.run(main())
