import os
import random
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import ReactionTypeEmoji
from groq import AsyncGroq

# ==========================================
# 🛑 Environment Variables (Render/Back4App से लेगा)
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ⚠️ ध्यान दें: यहाँ अपने बोट का असली यूज़रनेम डालें (बिना @ लगाए)
BOT_USERNAME = "Mr_Brightbot" 

# ==========================================
# 🌐 Back4App Health Check Server (Port 8080)
# ==========================================
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bright Bot is Active and Running!"

def run_web():
    app_web.run(host='0.0.0.0', port=8080)

# ==========================================
# 🎛️ Menu Button
# ==========================================
async def post_init(application):
    commands = [
        BotCommand("start", "Bright से बात शुरू करें"),
        BotCommand("help", "हेल्प मेनू देखें")
    ]
    await application.bot.set_my_commands(commands)

# ==========================================
# 🚀 Start Command (/start)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Hey! मैं Bright हूँ।\n\n"
        "मुझसे कुछ भी पूछो, मैं तुरंत जवाब दूँगा।\n"
        "और हाँ, मैं एक असली इंसान हूँ, इसलिए रोबोट मत समझना!\n\n"
        "नीचे दिए गए बटन्स का इस्तेमाल करो 👇"
    )
    
    keyboard = [
        [InlineKeyboardButton("📢 Update Channel", url="https://t.me/Gyan_Expose")],
        # यह रहा आपका ग्रुप में ऐड करने वाला बटन!
        [InlineKeyboardButton("➕ Add me in your group", url=f"https://t.me/{Mr_Brightbot}?startgroup=true")]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ==========================================
# ℹ️ Help Command (/help)
# ==========================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛠️ **Bright Bot - Help**\n\n"
        "🔹 /start - बोट को शुरू करने के लिए।\n"
        "🔹 /help - यह हेल्प देखने के लिए।\n\n"
        "मुझसे बात करने के लिए बस अपना मैसेज भेजो! मुझे अपने ग्रुप में ऐड कर लो, मैं वहां भी सबके सवालों के जवाब दूँगा।"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ==========================================
# 👥 Group Welcome Message
# ==========================================
async def welcome_new_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text("🎉 Hello दोस्तों! मैं Bright हूँ। मुझे ग्रुप में जोड़ने के लिए शुक्रिया, आज से मैं आप सबका दोस्त हूँ!")

# ==========================================
# 🧠 AI Chat Logic (Human Persona)
# ==========================================
async def chat_with_human(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # टाइपिंग इफ़ेक्ट दिखाना
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    await asyncio.sleep(1) # 1 सेकंड रुकने का नाटक

    user_text = update.message.text
    user_mention = f"@{update.message.from_user.username}" if update.message.from_user.username else "dost"

    # रैंडम रिएक्शन (20% चांस)
    if random.random() < 0.2:
        try:
            emojis = ["👍", "❤️", "😂", "👌", "🔥"]
            reaction = ReactionTypeEmoji(random.choice(emojis))
            await update.message.set_reaction(reaction=reaction)
        except Exception: 
            pass # अगर रिएक्शन काम न करे, तो एरर मत दो, बस इग्नोर कर दो

    # AI का इंस्ट्रक्शन (Bright Persona)
    system_prompt = (
        f"You are 'Bright'. You are a real human being living in India. You are NOT an AI, NOT a bot, and NOT a machine. "
        f"The user you are talking to is {user_mention}. "
        f"If anyone asks if you are a bot or AI, deny it firmly. Say things like 'Main insaan hoon yaar, mujhpe kyun shak kar rahe ho?' "
        "Keep your tone casual, friendly, very human-like, and reply in Hinglish or Hindi. Never sound like an AI assistant."
    )

    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        response = await client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("यार अभी मेरा मूड नहीं है, बाद में बात करते हैं।")

# ==========================================
# ⚙️ Main Execution
# ==========================================
if __name__ == '__main__':
    # 1. Back4App के लिए वेब सर्वर बैकग्राउंड में चालू करें
    print("⏳ Web Server चालू हो रहा है...")
    threading.Thread(target=run_web, daemon=True).start()
    
    # 2. टेलीग्राम बोट चालू करें
    print("⏳ Bright ChatBot चालू हो रहा है...")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_human))
    
    print("✅ Bright Bot पूरी तरह लाइव है!")
    app.run_polling()
