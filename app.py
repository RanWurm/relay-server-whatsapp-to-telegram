from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from telethon import TelegramClient
import asyncio
import threading

# Load environment variables from .env file (for local development)
load_dotenv()

app = Flask(__name__)

# Telegram credentials
API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
SESSION_NAME = os.environ.get('SESSION_NAME')
TARGET_CHAT = os.environ.get('TARGET_CHAT')

# Global client instance
client = None
loop = None

# Initialize Telethon client
def init_client():
    global client, loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH, loop=loop)
    
    # Start the client
    loop.run_until_complete(client.connect())
    if not loop.run_until_complete(client.is_user_authorized()):
        print("WARNING: User is not authorized. You need to run this locally first to authorize.")
    
    print("Telethon client initialized")
    
    # Keep the loop running
    threading.Thread(target=loop.run_forever, daemon=True).start()

# Start the client when the app initializes
init_client()

@app.route('/relay', methods=['POST'])
def relay_message():
    """Simple endpoint that forwards WhatsApp messages to Telegram using Telethon"""
    try:
        # Get message from WhatsApp bot
        message_data = request.get_json()
        
        # Format message as text
        if isinstance(message_data, str):
            telegram_message = f"📱 WhatsApp Message:\n\n{message_data}"
        else:
            telegram_message = f"📱 WhatsApp Message:\n\n{str(message_data)}"
        
        # Use the global loop to schedule the message sending
        asyncio.run_coroutine_threadsafe(
            client.send_message(TARGET_CHAT, telegram_message),
            loop
        )
        
        return jsonify({"success": True, "message": "Message forwarded to Telegram"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "client_connected": client.is_connected() if client else False
    })

# For local development
if __name__ == '__main__':
    app.run(debug=True)