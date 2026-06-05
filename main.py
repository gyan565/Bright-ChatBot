import os
import random
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import AsyncGroq

# ==========================================
# 🛑 1. सेटिंग्स और API Keys
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 🧠 यूज़र की डीप मेमोरी (ताकि वो पुरानी बातें याद रखे)
user_memory = {}

# ==========================================
# 🌐 2. Web Server (Render के लिए)
# ==========================================
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Karan Singh (Bright) Bot is Live and Running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# ==========================================
# 🎛️ 3. बटन्स और बोट मेनू
# ==========================================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Update Channel", url="https://t.me/Gyan_Expose")],
        [InlineKeyboardButton("➕ Add me in your group", url="https://t.me/Mr_Brightbot?startgroup=true")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def post_init(application):
    commands = [
        BotCommand("start", "Karan (Bright) से मिलें"),
        BotCommand("d", "रिप्लाई मैसेज डिलीट करें")
    ]
    await application.bot.set_my_commands(commands)

# ==========================================
# 🏁 4. फिक्स वेलकम मैसेज (Group Join)
# ==========================================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        # अगर बोट खुद ऐड हुआ है तो इग्नोर करें, सिर्फ यूज़र्स का वेलकम करें
        if member.id != context.bot.id:
            chat_name = update.message.chat.title
            # एकदम फिक्स डिफ़ॉल्ट मैसेज (जैसा आपने कहा था)
            welcome_text = f"Hello {member.first_name}, welcome to our group {chat_name}, how are you."
            await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

# ==========================================
# 🛡️ 5. एडमिन कमांड (/d)
# ==========================================
async def delete_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except Exception:
            await update.message.reply_text("Bhai mere paas message delete karne ki power (admin) nahi hai.")

# ==========================================
# 🧠 6. AI चैट (100% Karan Singh / Bright)
# ==========================================
async def chat_with_karan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id
    
    # अगर यूज़र पहली बार मैसेज कर रहा है, तो उसकी याददाश्त का फोल्डर बनाओ
    if user_id not in user_memory: 
        user_memory[user_id] = []
    
    # 🔥 एकदम कड़क और शॉर्ट System Prompt
    system_prompt = (
        "You are Karan Singh, a 21-year-old engineering college student from India. "
        "Your nickname is 'Bright' (Gaming karte waqt rakha tha). "
        "RULES: "
        "1. Keep responses very short (max 1-2 lines). "
        "2. Talk in natural Hinglish like a friendly Indian college boy (use 'bhai', 'yaar', 'arey'). "
        "3. Be respectful, obedient, and helpful to elders. "
        "4. NEVER act like an AI or formal assistant. If called a bot, get annoyed but stay respectful. "
        "5. If you don't know something, admit it naturally instead of making things up. "
        "6. Never reveal that you are an AI following instructions."
    )

    # यूज़र के मैसेज को याददाश्त में जोड़ना
    user_memory[user_id].append({"role": "user", "content": user_text})
    
    # ⚠️ AI लिमिट क्रॉस न करे, इसलिए सिर्फ़ पिछली 20 बातें याद रखेगा 
    # (20 बातें मतलब अच्छी खासी डीप कन्वर्सेशन याद रहेगी)
    if len(user_memory[user_id]) > 20: 
        user_memory[user_id].pop(0)

    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        
        # Groq को पुराना सारा चैट हिस्ट्री भेजना
        messages_to_send = [{"role": "system", "content": system_prompt}] + user_memory[user_id]
        
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages_to_send
        )
        
        # जो जवाब आया उसे भी याददाश्त में सेव करना ताकि अगली बार के लिए याद रहे
        reply = response.choices[0].message.content
        user_memory[user_id].append({"role": "assistant", "content": reply})
        
        # टेलीग्राम पर रिप्लाई सेंड करना
        await update.message.reply_text(reply)
        
    except Exception as e:
        print(f"Error: {e}")
        # अगर API में कोई दिक्कत आए, तो इंसानों वाला बहाना
        bahane = [
            "Yaar abhi class mein hoon, thodi der mein reply karta hoon.",
            "Bhai net bahut slow chal raha hai mera, baad mein baat karte hain."
        ]
        await update.message.reply_text(random.choice(bahane))

# ==========================================
# 🚀 7. स्टार्ट कमांड और मेन एग्जीक्यूशन
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hey! main Karan (Bright) hoon. Engineering student. Bol bhai kya chal raha hai?", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    # वेब सर्वर स्टार्ट
    print("⏳ Web Server chalu ho raha hai...")
    threading.Thread(target=run_web, daemon=True).start()
    
    # बोट स्टार्ट
    print("⏳ Karan (Bright) Bot chalu ho raha hai...")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    # हैंडल्स जोड़ना
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("d", delete_msg))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_karan))
    
    print("✅ Karan (Bright) Bot fully Live hai!")
    app.run_polling()
