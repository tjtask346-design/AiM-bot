import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

class AiMBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = "gemini-2.0-flash-001"
    
    def get_response(self, message):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": f"You are AiM, an AI assistant. Help the user and answer their questions. Always identify yourself as AiM. Question: {message}"
                    }]
                }]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=60)
            
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "Sorry, I cannot generate a response right now."
            
            else:
                return self.fallback_model(message)
                
        except requests.exceptions.Timeout:
            return "Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return "Connection error. Please check your internet connection."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def fallback_model(self, message):
        fallback_models = [
            "gemini-2.0-flash-lite-001",
            "gemini-flash-latest",
            "gemini-pro-latest"
        ]
        
        for model in fallback_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                
                data = {
                    "contents": [{
                        "parts": [{
                            "text": f"You are AiM, an AI assistant. Help the user and answer their questions. Always identify yourself as AiM. Question: {message}"
                        }]
                    }]
                }
                
                response = requests.post(url, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and result['candidates']:
                        print(f"Fallback successful with model: {model}")
                        return result['candidates'][0]['content']['parts'][0]['text']
                        
            except Exception as e:
                continue
        
        return "Sorry, I'm having trouble connecting to the AI service. Please try again later."

GEMINI_API_KEY = "AIzaSyCxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TELEGRAM_TOKEN = "1234567890:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

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
    
    print(f"Message from user {user_id}: {user_message}")
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="typing"
    )
    
    try:
        bot_response = aim_bot.get_response(user_message)
        
        print(f"Bot response: {bot_response}")
        
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        error_msg = f"Sorry, an error occurred: {str(e)}"
        await update.message.reply_text(error_msg)
        print(f"Error: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Telegram bot error: {context.error}")
    if update and update.message:
        await update.message.reply_text("Sorry, something went wrong. Please try again.")

def main():
    print("Starting AiM Telegram Bot...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error_handler)
    
    print("✅ AiM Bot is ready and running!")
    print("📱 Go to Telegram and send /start to your bot")
    
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=30
    )

if __name__ == "__main__":
    main()
