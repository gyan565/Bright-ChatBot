import os
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ReactionEmoji
from groq import AsyncGroq

# Environment variables (Render/Local par set karna zaroori hai)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BOT_USERNAME = "Mr_Brightbot" 

client = AsyncGroq(api_key=GROQ_API_KEY)

# Reaction list
REACTIONS = [ReactionEmoji.THUMBS_UP, ReactionEmoji.HEART, ReactionEmoji.LAUGHING, ReactionEmoji.OK_HAND]

async def post_init(application):
    commands = [
        BotCommand("start", "Start"),
        BotCommand("help", "Help")
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Hey! Main Bright hoon.\n\n"
        "Mujhse kuch bhi poocho, main help karunga.\n"
        "Main ek insaan hoon, toh aaram se baat karo!"
    )
    keyboard = [
        [InlineKeyboardButton("📢 Channel", url="https://t.me/Gyan_Expose")],
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{Mr_Brightbot}?startgroup=true")]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bas mujhse seedha baat karo, main sab bata dunga!")

async def welcome_new_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text("Hello doston! Kaise ho sab? Main Bright hoon, aaj se aapka dost!")

async def chat_with_human(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Typing effect dikhao
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    await asyncio.sleep(1.5) # Thoda time rukne ka natak (Taaki insaan lage)

    user_text = update.message.text
    user_mention = f"@{update.message.from_user.username}" if update.message.from_user.username else "dost"

    # 2. Random Reaction (20% chance)
    if random.random() < 0.2:
        try:
            await update.message.set_reaction(reaction=random.choice(REACTIONS))
        except: pass

    # 3. System Prompt (The Persona)
    system_prompt = (
        f"You are 'Bright'. You are a real human being. You are NOT an AI, NOT a bot, and NOT a machine. "
        f"The user you are talking to is {user_mention}. "
        f"If anyone asks if you are a bot/AI, deny it firmly. Say something like 'Main insaan hoon yaar, mujhpe kyun shak kar rahe ho?' or 'Bot? Seriously? Main insaan hoon.'. "
        "Keep your tone casual, friendly, and very human-like. Use slang if needed. Never sound robotic."
    )

    try:
        response = await client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text("Yaar abhi mood nahi hai baad me baat karte hain.")

# Imports में ये जोड़ें
from flask import Flask
import threading

# 💡 एक छोटा सा वेब सर्वर जो Back4App को खुश रखेगा
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bright Bot is active!"

def run_web():
    app_web.run(host='0.0.0.0', port=8080)

# ⚙️ Main execution में ये बदलाव करें
if __name__ == '__main__':
    # वेब सर्वर को बैकग्राउंड में चलाएं
    threading.Thread(target=run_web).start()
    
    # अब बोट को चलाएं
    print("⏳ Bright ChatBot चालू हो रहा है...")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    # ... (बाकी का कोड वैसे ही रहने दें)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_human))
    app.run_polling()
