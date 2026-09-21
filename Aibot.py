```python
import os
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, ReplyKeyboardMarkup
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
# УКРАИНСКИЙ ИНТЕРФЕЙС
# =========================

keyboard = [
    ["💬 Поставити запитання"],
    ["🎙️ Голосовий помічник"],
    ["🌐 Мова"],
    ["ℹ️ Про бота"]
]

reply_keyboard = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True
)


# =========================
# /start
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🇺🇦 Вітаю!\n\n"
        "Я твій AI-помічник.\n\n"
        "💬 Можеш поставити мені запитання.\n"
        "🎙️ Можеш надіслати голосове повідомлення.\n"
        "🌍 Я можу спілкуватися різними мовами.\n\n"
        "Просто напиши мені повідомлення 👇",
        reply_markup=reply_keyboard
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
                    "Ти дружній універсальний AI-помічник. "
                    "Відповідай зрозуміло, корисно та природно.\n\n"

                    "ВАЖЛИВО:\n"
                    "1. Визначай мову повідомлення користувача.\n"
                    "2. Відповідай тією самою мовою.\n"
                    "3. Якщо користувач пише українською — "
                    "відповідай українською.\n"
                    "4. Якщо користувач пише англійською — "
                    "відповідай англійською.\n"
                    "5. Якщо користувач пише німецькою — "
                    "відповідай німецькою.\n"
                    "6. Якщо користувач пише польською — "
                    "відповідай польською.\n"
                    "7. Якщо користувач використовує іншу мову — "
                    "намагайся відповідати цією ж мовою.\n"
                    "8. Не перекладай запит без потреби.\n"
                    "9. Не повідомляй користувачу, яку мову ти визначив."
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
# ТЕКСТОВІ ПОВІДОМЛЕННЯ
# =========================

async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        question = update.message.text

        print("Користувач:", question)

        # Кнопки інтерфейсу
        if question == "💬 Поставити запитання":

            await update.message.reply_text(
                "💬 Напиши своє запитання 👇"
            )
            return

        if question == "🎙️ Голосовий помічник":

            await update.message.reply_text(
                "🎙️ Надішли мені голосове повідомлення, "
                "і я його розпізнаю."
            )
            return

        if question == "🌐 Мова":

            await update.message.reply_text(
                "🌐 Мову відповіді я визначаю автоматично.\n\n"
                "Напиши українською — відповім українською.\n"
                "Write in English — I will answer in English.\n"
                "Schreib auf Deutsch — ich antworte auf Deutsch.\n"
                "Napisz po polsku — odpowiem po polsku."
            )
            return

        if question == "ℹ️ Про бота":

            await update.message.reply_text(
                "🤖 AI-помічник\n\n"
                "💬 Розуміє текстові повідомлення\n"
                "🎙️ Розпізнає голосові повідомлення\n"
                "🌍 Підтримує різні мови\n"
                "🇺🇦 Має український інтерфейс"
            )
            return

        # Запит до AI
        answer = ask_ai(question)

        await update.message.reply_text(
            answer
        )

    except Exception as e:

        print(
            "Помилка AI:",
            repr(e)
        )

        await update.message.reply_text(
            "❌ Сталася помилка під час звернення до AI."
        )


# =========================
# ГОЛОСОВІ ПОВІДОМЛЕННЯ
# =========================

async def voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        await update.message.reply_text(
            "🎙️ Слухаю..."
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
            "Розпізнано:",
            recognized_text
        )

        await update.message.reply_text(
            "📝 Я почув:\n\n"
            + recognized_text
        )

        # Передаємо розпізнаний текст AI
        answer = ask_ai(
            recognized_text
        )

        await update.message.reply_text(
            answer
        )

    except Exception as e:

        print(
            "Помилка голосу:",
            repr(e)
        )

        await update.message.reply_text(
            "❌ Не вдалося розпізнати голосове повідомлення."
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

    # Голосові повідомлення
    app.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_message
        )
    )

    # Текстові повідомлення
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message
        )
    )

    print(
        "🤖 AI-помічник запущений!"
    )

    print(
        "🇺🇦 Український інтерфейс: OK"
    )

    print(
        "🌍 Багатомовний режим: OK"
    )

    print(
        "🎙️ Голос: OK"
    )

    app.run_polling()


# =========================
# START
# =========================
```
