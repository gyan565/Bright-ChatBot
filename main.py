import os
import random
import asyncio
import threading
import json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import AsyncGroq

# ==========================================
# 🛑 1. सेटिंग्स और API Keys
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ADMIN_ID वो है जो ब्रॉडकास्ट कर सकता है (आपकी खुद की टेलीग्राम ID)
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

user_memory = {}
CHATS_FILE = "chats.json"

# ==========================================
# 💾 2. लोकल फाइल में ID सेव करने का जुगाड़
# ==========================================
def get_saved_chats():
    try:
        with open(CHATS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_chat_id(chat_id):
    chats = get_saved_chats()
    if chat_id not in chats:
        chats.append(chat_id)
        with open(CHATS_FILE, "w") as f:
            json.dump(chats, f)

# ==========================================
# 🌐 3. Web Server (Render)
# ==========================================
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Karan Singh (Bright) Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# ==========================================
# 🎛️ 4. बटन्स और मेनू
# ==========================================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Update Channel", url="https://t.me/BrightUpdates")],
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
# 📢 5. ब्रॉडकास्ट कमांड (/bcast)
# ==========================================
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # सिर्फ एडमिन (आप) ही ब्रॉडकास्ट कर सकते हैं
    if user_id != ADMIN_ID:
        await update.message.reply_text("Bhai tu admin thodi hai jo broadcast karega! 😂")
        return

    # मैसेज से '/bcast ' हटाकर असली मैसेज निकालना
    command_text = update.message.text
    if len(command_text.split()) < 2:
        await update.message.reply_text("Bhai format galat hai. Aise likh: /bcast Hello dosto!")
        return
        
    bcast_msg = command_text.replace("/bcast ", "", 1)
    
    chats = get_saved_chats()
    success = 0
    
    await update.message.reply_text(f"⏳ Broadcast shuru ho gaya... {len(chats)} logo/groups ko bhejna hai.")
    
    for chat_id in chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=bcast_msg)
            success += 1
            await asyncio.sleep(0.1) # Telegram block na kare isliye chhota sa delay
        except Exception:
            pass # Agar kisi ne bot block kar diya ho to error skip karega
            
    await update.message.reply_text(f"✅ Broadcast Done! {success} logo/groups tak message pahunch gaya.")

# ==========================================
# 🏁 6. फिक्स वेलकम मैसेज (Group Join)
# ==========================================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id) # ग्रुप की ID सेव कर लो
    
    for member in update.message.new_chat_members:
        if member.id != context.bot.id:
            chat_name = update.message.chat.title
            welcome_text = f"Hello {member.first_name}, welcome to our group {chat_name}, how are you."
            await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

# ==========================================
# 🛡️ 7. एडमिन डिलीट कमांड (/d)
# ==========================================
async def delete_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except Exception:
            await update.message.reply_text("Bhai admin power nahi hai mere paas.")

# ==========================================
# 🧠 8. AI चैट (Karan Singh) + Typing Effect
# ==========================================
async def chat_with_karan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id
    
    save_chat_id(chat_id) # बात करने वाले यूज़र या ग्रुप की ID सेव कर लो
    
    if user_id not in user_memory: 
        user_memory[user_id] = []
    
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

    user_memory[user_id].append({"role": "user", "content": user_text})
    if len(user_memory[user_id]) > 20: 
        user_memory[user_id].pop(0)

    # 🔥 इंसानों वाला Typing Effect
    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
    await asyncio.sleep(1.5) # 1.5 सेकंड का नाटक

    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        messages_to_send = [{"role": "system", "content": system_prompt}] + user_memory[user_id]
        
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages_to_send
        )
        
        reply = response.choices[0].message.content
        user_memory[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
        
    except Exception as e:
        bahane = [
            "Yaar abhi class mein hoon, thodi der mein reply karta hoon.",
            "Bhai net bahut slow chal raha hai mera, baad mein baat karte hain."
        ]
        await update.message.reply_text(random.choice(bahane))

# ==========================================
# 🚀 9. स्टार्ट कमांड
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id) # स्टार्ट करने वाले की ID सेव
    await update.message.reply_text("👋 Hey! main Karan (Bright) hoon. Engineering student. Bol bhai kya chal raha hai?", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bcast", broadcast_message)) # नया ब्रॉडकास्ट हैंडलर
    app.add_handler(CommandHandler("d", delete_msg))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_karan))
    
    print("✅ Karan Bot Live hai with Broadcast & Typing Effect!")
    app.run_polling()
