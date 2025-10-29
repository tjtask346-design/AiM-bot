import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am AiM, your AI assistant. How can I help you today?')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Available commands:
/start - Start the bot
/help - Show help
"""
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    try:
        prompt = f"Respond naturally as AiM AI assistant: {user_message}"
        response = model.generate_content(prompt)
        
        if response.text:
            if len(response.text) > 4096:
                for i in range(0, len(response.text), 4096):
                    await update.message.reply_text(response.text[i:i+4096])
            else:
                await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("I apologize, but I couldn't generate a response at the moment.")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Sorry, I'm experiencing some technical issues. Please try again later.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("Bot is running...")
    app.run_polling(poll_interval=3)
