import os
import asyncio
import io

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from pypdf import PdfReader
from docx import Document

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# ==========================================
# НАСТРОЙКИ
# ==========================================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

CHAT_MODEL = "openai/gpt-oss-120b"
VOICE_MODEL = "openai/whisper-large-v3"


# ==========================================
# ПРОВЕРКА ТОКЕНОВ
# ==========================================

if not TELEGRAM_TOKEN:
    raise ValueError(
        "Не найден TELEGRAM_TOKEN. "
        "Добавь его в Railway Variables."
    )

if not HF_TOKEN:
    raise ValueError(
        "Не найден HF_TOKEN. "
        "Добавь его в Railway Variables."
    )


# ==========================================
# HUGGING FACE
# ==========================================

client = InferenceClient(
    api_key=HF_TOKEN
)


# ==========================================
# КЛАВИАТУРА
# ==========================================

keyboard = [
    ["💬 Поставити запитання"],
    ["🎙️ Голосовий помічник"],
    ["📄 Робота з файлами"],
    ["🌐 Мова"],
    ["ℹ️ Про бота"],
]

reply_keyboard = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True
)


# ==========================================
# ХРАНИЛИЩЕ ТЕКСТА ФАЙЛА
# ==========================================

# Здесь будем хранить последний загруженный
# файл для каждого пользователя.

user_files = {}


# ==========================================
# START
# ==========================================

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
        "• читати PDF, DOCX та TXT файли;\n"
        "• відповідати на запитання за вмістом файлів.\n\n"

        "📄 Надішли мені файл, а потім запитай, "
        "що в ньому знаходиться.\n\n"

        "🎙️ Також можеш надіслати голосове повідомлення."
    )

    await update.message.reply_text(
        text,
        reply_markup=reply_keyboard
    )


# ==========================================
# AI
# ==========================================

async def ask_ai(
    question: str,
    file_text: str = None
) -> str:

    try:

        system_prompt = (
            "Ти дружелюбний багатомовний AI-помічник. "
            "Відповідай зрозуміло, корисно та природно. "

            "ВАЖЛИВО: визнач мову повідомлення користувача "
            "та відповідай тією ж мовою. "

            "Якщо користувач пише українською — відповідай "
            "українською. "

            "Якщо російською — російською. "

            "Якщо англійською — англійською. "

            "Якщо іншою мовою — намагайся відповідати "
            "цією ж мовою."
        )

        # Если пользователь загрузил файл
        if file_text:

            system_prompt += (
                "\n\nУ користувача є файл. "
                "Текст файлу наведено нижче.\n\n"

                "ТЕКСТ ФАЙЛУ:\n"
                "--------------------\n"
                f"{file_text}\n"
                "--------------------\n\n"

                "Використовуй цей текст, щоб відповідати "
                "на запитання користувача про файл. "

                "Не вигадуй інформацію, якої немає у файлі. "
                "Якщо відповіді у файлі немає, прямо скажи про це."
            )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ]

        response = client.chat_completion(
            messages=messages,
            model=CHAT_MODEL,
            max_tokens=1500,
            temperature=0.7
        )

        answer = response.choices[0].message.content

        if not answer:
            return "❌ AI не зміг сформувати відповідь."

        return answer

    except Exception as e:

        print("AI ERROR:", e)

        return (
            "❌ Сталася помилка під час звернення до AI."
        )


# ==========================================
# ЧТЕНИЕ TXT
# ==========================================

def read_txt(data: bytes) -> str:

    try:
        return data.decode("utf-8")

    except UnicodeDecodeError:

        try:
            return data.decode("cp1251")

        except Exception:
            return data.decode(
                "utf-8",
                errors="ignore"
            )


# ==========================================
# ЧТЕНИЕ PDF
# ==========================================

def read_pdf(data: bytes) -> str:

    pdf_file = io.BytesIO(data)

    reader = PdfReader(pdf_file)

    text = []

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text.append(page_text)

    return "\n\n".join(text)


# ==========================================
# ЧТЕНИЕ DOCX
# ==========================================

def read_docx(data: bytes) -> str:

    doc_file = io.BytesIO(data)

    document = Document(doc_file)

    text = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            text.append(paragraph.text)

    return "\n".join(text)


# ==========================================
# ОБРАБОТКА ФАЙЛОВ
# ==========================================

async def file_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.document:
        return

    document = update.message.document

    file_name = document.file_name or "unknown"

    extension = os.path.splitext(
        file_name
    )[1].lower()

    supported_files = [
        ".txt",
        ".pdf",
        ".docx"
    ]

    if extension not in supported_files:

        await update.message.reply_text(
            "❌ Я пока не вмію читати цей формат.\n\n"
            "Підтримуються:\n"
            "📄 TXT\n"
            "📕 PDF\n"
            "📝 DOCX"
        )

        return

    try:

        await update.message.reply_text(
            "📥 Отримав файл.\n"
            "⏳ Читаю його..."
        )

        # Получаем Telegram-файл
        telegram_file = await document.get_file()

        # Загружаем в память
        file_data = await telegram_file.download_as_bytearray()

        file_bytes = bytes(file_data)

        # Читаем файл
        if extension == ".txt":

            text = read_txt(file_bytes)

        elif extension == ".pdf":

            text = read_pdf(file_bytes)

        elif extension == ".docx":

            text = read_docx(file_bytes)

        else:

            text = ""

        if not text.strip():

            await update.message.reply_text(
                "❌ Я не зміг знайти текст у цьому файлі."
            )

            return

        # Ограничиваем размер текста,
        # чтобы не перегружать AI
        max_chars = 50000

        if len(text) > max_chars:

            text = text[:max_chars]

            text += (
                "\n\n[Текст файлу обрізано через "
                "великий розмір.]"
            )

        # Сохраняем файл пользователя
        user_id = update.effective_user.id

        user_files[user_id] = {
            "name": file_name,
            "text": text
        }

        await update.message.reply_text(
            f"✅ Файл «{file_name}» прочитано!\n\n"
            "📄 Тепер можеш запитати мене, "
            "що знаходиться у файлі.\n\n"
            "Наприклад:\n"
            "• Що знаходиться в цьому файлі?\n"
            "• Коротко перекажи його.\n"
            "• Які головні думки?\n"
            "• Поясни простими словами."
        )

    except Exception as e:

        print("FILE ERROR:", e)

        await update.message.reply_text(
            "❌ Не вдалося прочитати файл.\n"
            "Перевір, що файл не пошкоджений."
        )


# ==========================================
# ТЕКСТОВЫЕ СООБЩЕНИЯ
# ==========================================

async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user_text = update.message.text

    # Кнопка вопроса
    if user_text == "💬 Поставити запитання":

        await update.message.reply_text(
            "💬 Напиши своє запитання."
        )

        return

    # Голос
    if user_text == "🎙️ Голосовий помічник":

        await update.message.reply_text(
            "🎙️ Надішли мені голосове повідомлення."
        )

        return

    # Файлы
    if user_text == "📄 Робота з файлами":

        await update.message.reply_text(
            "📄 Надішли мені TXT, PDF або DOCX файл.\n\n"
            "Після цього можеш запитати:\n"
            "«Що знаходиться в цьому файлі?»"
        )

        return

    # Язык
    if user_text == "🌐 Мова":

        await update.message.reply_text(
            "🌍 Я автоматично визначаю мову "
            "твого повідомлення та відповідаю "
            "тією ж мовою."
        )

        return

    # О боте
    if user_text == "ℹ️ Про бота":

        await update.message.reply_text(
            "🤖 AI-помічник\n\n"
            "🇺🇦 Український інтерфейс\n"
            "🌍 Багатомовні відповіді\n"
            "🎙️ Голосове розпізнавання\n"
            "📄 Читання TXT / PDF / DOCX\n"
            "🧠 Hugging Face AI"
        )

        return

    # Проверяем, есть ли файл
    user_id = update.effective_user.id

    file_info = user_files.get(user_id)

    file_text = None

    if file_info:
        file_text = file_info["text"]

    # Показываем typing
    await update.message.chat.send_action(
        action="typing"
    )

    answer = await ask_ai(
        user_text,
        file_text
    )

    await update.message.reply_text(answer)


# ==========================================
# ГОЛОС
# ==========================================

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

        voice_file = await update.message.voice.get_file()

        audio_data = await voice_file.download_as_bytearray()

        transcription = client.automatic_speech_recognition(
            audio=bytes(audio_data),
            model=VOICE_MODEL
        )

        recognized_text = transcription.text

        if not recognized_text:

            await update.message.reply_text(
                "❌ Не вдалося розпізнати голос."
            )

            return

        await update.message.reply_text(
            f"📝 Я почув:\n\n"
            f"{recognized_text}\n\n"
            "🤖 Думаю над відповіддю..."
        )

        # Проверяем, есть ли загруженный файл
        user_id = update.effective_user.id

        file_info = user_files.get(user_id)

        file_text = None

        if file_info:
            file_text = file_info["text"]

        answer = await ask_ai(
            recognized_text,
            file_text
        )

        await update.message.reply_text(answer)

    except Exception as e:

        print("VOICE ERROR:", e)

        await update.message.reply_text(
            "❌ Не вдалося обробити голосове повідомлення."
        )


# ==========================================
# ЗАПУСК
# ==========================================

async def main():

    app = (
        Application
        .builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Файлы
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            file_message
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

    print("=================================")
    print("🤖 AI-помічник запущений!")
    print("🇺🇦 Український інтерфейс: OK")
    print("🌍 Багатомовний режим: OK")
    print("🎙️ Голосовий режим: OK")
    print("📄 Робота з файлами: OK")
    print("🚂 Railway mode: OK")
    print("=================================")

    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    await asyncio.Event().wait()


# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    asyncio.run(main())
