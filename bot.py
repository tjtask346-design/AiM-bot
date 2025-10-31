import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AiMBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = "gemini-2.0-flash-001"

    def get_response(self, message):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

            # উন্নত প্রম্পট
            prompt = f"""You are AiM (pronounced as "Aim"), an AI assistant.
Always identify yourself as "AiM" (never write it in Bengali script).
Help the user and answer their questions clearly and concisely.

User question: {message}"""

            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1024,
                }
            }

            headers = {
                "Content-Type": "application/json"
            }

            # কম টাইমআউট সহ রিকোয়েস্ট
            response = requests.post(url, json=data, headers=headers, timeout=45)

            logger.info(f"API Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                    # AiM নাম যাতে বাংলায় না লিখে
                    response_text = response_text.replace('এআইএম', 'AiM').replace('এআইএম', 'AiM')
                    return response_text
                else:
                    return "Sorry, I cannot generate a response right now."
            else:
                logger.warning(f"Primary model failed, trying fallback. Status: {response.status_code}")
                return self.fallback_model(message)

        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return "Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            return "Connection error. Please check your internet connection."
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            return self.fallback_model(message)

    def fallback_model(self, message):
        fallback_models = [
            "gemini-2.0-flash-lite-001",
            "gemini-flash-latest",
            "gemini-pro-latest"
        ]

        for model in fallback_models:
            try:
                logger.info(f"Trying fallback model: {model}")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"

                prompt = f"""You are AiM (pronounced as "Aim"), an AI assistant.
Always identify yourself as "AiM" (never write it in Bengali script).
Help the user and answer their questions.

User question: {message}"""

                data = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 1024,
                    }
                }

                response = requests.post(url, json=data, timeout=25)

                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and result['candidates']:
                        logger.info(f"Fallback successful with model: {model}")
                        response_text = result['candidates'][0]['content']['parts'][0]['text']
                        response_text = response_text.replace('এআইএম', 'AiM').replace('এআইএম', 'AiM')
                        return response_text

            except Exception as e:
                logger.warning(f"Fallback model {model} failed: {str(e)}")
                continue

        return "Sorry, I'm having trouble connecting to the AI service. Please try again later."

GEMINI_API_KEY = "AIzaSyChmo0ZnnPBi6YZMGqxszB-XotQu54nmzY"
TELEGRAM_TOKEN = "8420755928:AAEp2yxrqPK9-g9SPhxRHL4hLlqr9x7HX9o"

aim_bot = AiMBot(GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    welcome_text = f"""
🤖 Hello {user_name}! I'm AiM, your AI assistant.

I can help you with:
• Answering questions
• Creative writing
• Problem solving
• Information and explanations
• And much more!

Just send me a message and I'll respond!
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 Help Guide

• Just send me any message and I'll respond
• I can answer questions, help with writing, solve problems
• I support long conversations with context
• If I don't respond, try sending your message again

Commands:
/start - Start the bot
/help - Show this help message
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id

    logger.info(f"Message from user {user_id}: {user_message}")

    # টাইপিং ইন্ডিকেটর
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        # নন-ব্লকিং Way তে রেসপন্স নেওয়ার জন্য
        bot_response = await asyncio.get_event_loop().run_in_executor(
            None, aim_bot.get_response, user_message
        )

        logger.info(f"Bot response generated for user {user_id}")

        # লম্বা রেসপন্স কাটাছেঁড়া
        if len(bot_response) > 4096:
            chunks = [bot_response[i:i+4096] for i in range(0, len(bot_response), 4096)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
                await asyncio.sleep(0.5)
        else:
            await update.message.reply_text(bot_response)

    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        error_msg = "Sorry, an error occurred while processing your request. Please try again."
        await update.message.reply_text(error_msg)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Telegram bot error: {context.error}")
    if update and update.message:
        await update.message.reply_text("Sorry, something went wrong. Please try again.")

def main():
    logger.info("Starting AiM Telegram Bot...")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error_handler)

    logger.info("✅ AiM Bot is ready and running!")
    logger.info("📱 Go to Telegram and send /start to your bot")

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=60
    )

if __name__ == "__main__":
    main()
