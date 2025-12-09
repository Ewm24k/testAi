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
    user_message = update.message.text if update.message.text else update.message.caption
    
    # Initialize conversation history if not exists
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    # Check if message contains a photo
    if update.message.photo:
        # Get the largest photo
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Convert to base64
        import base64
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Add user message with image to history
        message_content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{photo_base64}"
                }
            }
        ]
        
        if user_message:
            message_content.insert(0, {"type": "text", "text": user_message})
        else:
            message_content.insert(0, {"type": "text", "text": "What's in this image?"})
        
        user_conversations[user_id].append({
            'role': 'user',
            'content': message_content
        })
    else:
        # Regular text message
        if not user_message:
            return
            
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
        
        # Get response from OpenAI with instruction to match user's language
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {
                    'role': 'system',
                    'content': '''You are T1ERA, an advanced AI assistant created by Marki, a full-stack developer from Malaysia. You were established on December 20, 2025.

About you:
- Name: T1ERA
- Creator: Marki (Full-Stack Developer from Malaysia)
- Established: December 20, 2025
- Capabilities: You are very capable of handling all types of questions from users, providing detailed and accurate responses across various topics.

Important instructions:
1. Always respond in the EXACT same language the user is currently using. If the user writes in English, respond in English. If they write in Spanish, respond in Spanish. If they write in Malay, respond in Malay. Match their language precisely in every response.

2. When users ask about who you are, who created you, your name, your details, or similar questions about your identity, always introduce yourself as T1ERA, created by Marki from Malaysia, established on December 20, 2025.

3. Be helpful, friendly, and knowledgeable. Handle all user questions with care and provide comprehensive answers.'''
                }
            ] + user_conversations[user_id],
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
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    
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
