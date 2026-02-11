import os
import logging
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai

# --- CONFIGURAZIONE VARIABILI ---
# Queste verranno lette dalle impostazioni di Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("GOOGLE_API_KEY")

# Configura Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- WEB SERVER PER UPTIMEROBOT ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web_server():
    # Render ci assegna una porta dinamica, usiamo quella o la 8080 di default
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# --- FUNZIONI DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ciao! Sono online e pronto.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Mostra "sta scrivendo..."
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')
    
    try:
        response = await model.generate_content_async(user_text)
        await context.bot.send_message(chat_id=chat_id, text=response.text)
    except Exception as e:
        print(f"Errore: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Mi dispiace, si è verificato un errore.")

# --- AVVIO ---
if __name__ == '__main__':
    # Avvia il server web in background
    keep_alive()
    
    # Avvia il bot
    if not TOKEN:
        print("ERRORE: Manca il Token Telegram!")
    else:
        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("Bot in avvio...")
        application.run_polling()
