import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set API keys
TELEGRAM_TOKEN = '8585326191:AAGWahXKfYW_FvyLtg5g8xDU_KdkHkX8QW0'
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

client = OpenAI(api_key=OPENAI_API_KEY)

# Store conversation history for each user
user_conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    
    await update.message.reply_text(
        'Hi! I\'m an AI assistant powered by OpenAI. Send me a message and I\'ll respond!\n\n'
        'Commands:\n'
        '/start - Start the bot\n'
        '/clear - Clear conversation history\n'
        '/help - Show this help message'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Just send me any message and I\'ll respond using OpenAI!\n\n'
        'Commands:\n'
        '/start - Start the bot\n'
        '/clear - Clear conversation history\n'
        '/help - Show this help message'
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear the conversation history."""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text('Conversation history cleared!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and respond using OpenAI."""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Initialize conversation history if not exists
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    # Add user message to history
    user_conversations[user_id].append({
        'role': 'user',
        'content': user_message
    })
    
    # Keep only last 10 messages to avoid token limits
    if len(user_conversations[user_id]) > 10:
        user_conversations[user_id] = user_conversations[user_id][-10:]
    
    try:
        # Send "typing..." action
        await update.message.chat.send_action(action="typing")
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=user_conversations[user_id],
            max_tokens=500
        )
        
        bot_response = response.choices[0].message.content
        
        # Add bot response to history
        user_conversations[user_id].append({
            'role': 'assistant',
            'content': bot_response
        })
        
        # Send response to user
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            f'Sorry, I encountered an error: {str(e)}\n'
            'Please try again later.'
        )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot with webhook for Render
    PORT = int(os.environ.get('PORT', 8443))
    RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
    
    if RENDER_EXTERNAL_URL:
        # Running on Render with webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}"
        )
    else:
        # Running locally with polling
        logger.info("Starting bot in polling mode...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
