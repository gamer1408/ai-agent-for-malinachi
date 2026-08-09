import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# 1. Environment (.env) faylini yuklash
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ Xatolik: .env faylida TELEGRAM_BOT_TOKEN yoki GEMINI_API_KEY topilmadi!")

# 2. system_prompt.txt faylini o'qish
prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
try:
    with open(prompt_path, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    raise FileNotFoundError("❌ Xatolik: system_prompt.txt fayli topilmadi!")

# 3. Gemini Client va Logging
ai_client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_SUFFIX = "\n\n*(🤖 AI yordamchi javobi)*"

# 4. Handler funksiyalari
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Assalomu alaykum, aka! 🌱\n"
        "Malinachi_ rasmiy AI maslahatchisiman. Sizga malina ko'chatlari, navlar va ekish-parvarishlash bo'yicha yordam berishdan xursandman!\n"
        "📢 Telegram kanalimiz: https://t.me/malinach_i\n"
        f"{BOT_SUFFIX}"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    models_to_try = [
        'gemini-3.5-flash',
        'gemini-3-flash-preview',
        'gemini-flash-latest'
    ]
    
    response = None
    last_error = None

    for model_name in models_to_try:
        try:
            response = ai_client.models.generate_content(
                model=model_name,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.4
                )
            )
            if response and response.text:
                logging.info(f"Muvaffaqiyatli ishlatilgan model: {model_name}")
                break
        except Exception as e:
            last_error = e
            logging.warning(f"Model {model_name} xatosi: {e}. Keyingisiga o'tilmoqda...")

    if response and response.text:
        reply_text = response.text.strip()
        
        # Har doim AI belgisi borligini ta'minlash
        if "*(🤖 AI yordamchi javobi)*" not in reply_text:
            reply_text = f"{reply_text}{BOT_SUFFIX}"
            
        await update.message.reply_text(reply_text)
    else:
        logging.error(f"Xatolik tafsiloti: {last_error}")
        error_msg = (
            "Aka, bu masalani to'g'ri hal qilishimiz uchun sizni bizning mutaxassisimizga ulashtirib qo'yay — "
            f"ular tez orada sizga javob beradi. @malinalar_uz manziliga murojaat qilishingiz mumkin 😊{BOT_SUFFIX}"
        )
        await update.message.reply_text(error_msg)

# 5. Botni yuritish
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Malinachi AI boti muvaffaqiyatli ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()