import os
import datetime
import threading
import json
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import AsyncGroq

# ==========================================
# 🛑 1. SETTINGS
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

user_memory = {}
CHATS_FILE = "chats.json"

# ==========================================
# 💾 2. JSON MEMORY
# ==========================================
def get_saved_chats():
    try:
        with open(CHATS_FILE, "r") as f: return json.load(f)
    except: return []

def save_chat_id(chat_id):
    chats = get_saved_chats()
    if chat_id not in chats:
        chats.append(chat_id)
        with open(CHATS_FILE, "w") as f: json.dump(chats, f)

# ==========================================
# 🌐 3. WEB SERVER (Render)
# ==========================================
app_web = Flask(__name__)
@app_web.route('/')
def home(): return "Karan Singh (Bright) Bot is Live!"
def run_web(): app_web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# ==========================================
# 🎛️ 4. BOT MENU & COMMANDS
# ==========================================
async def post_init(application):
    commands = [
        BotCommand("start", "Karan se baat shuru kar"),
        BotCommand("help", "Kya kya kar sakta hoon main"),
        BotCommand("d", "Message uda de (Reply karke)")
    ]
    await application.bot.set_my_commands(commands)

# ==========================================
# 🛑 5. HELP COMMAND (/help)
# ==========================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Bhai dekh, main tera dost Karan hoon. Ye rahi meri powers:\n\n"
        "👉 `/start` - Mujhse baat shuru karne ke liye.\n"
        "👉 `/help` - Ye list dekhne ke liye (jo tu abhi dekh raha hai).\n"
        "👉 `/d` - Kisi faltu message par reply karke /d likh, main usko aur apne message dono ko uda dunga (Admin power chahiye).\n"
        "👉 `/bcast` - Sirf Admin ke liye! Sabko ek sath message bhejne ke liye (Format: /bcast Hello Dosto).\n\n"
        "Baaki normal chat karni hai toh mujhe tag kar (@TeraBotUsername) ya mere message ka reply kar! 🔥"
    )
    await update.message.reply_text(help_text, parse_mode=constants.ParseMode.MARKDOWN)

# ==========================================
# 📢 6. BROADCAST COMMAND (/bcast)
# ==========================================
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Bhai tu admin thodi hai jo broadcast karega! 😂")
        return

    command_text = update.message.text
    if len(command_text.split()) < 2:
        await update.message.reply_text("Bhai aise likh: /bcast Hello dosto!")
        return
        
    bcast_msg = command_text.replace("/bcast ", "", 1)
    chats = get_saved_chats()
    success = 0
    
    await update.message.reply_text(f"⏳ Broadcast shuru... {len(chats)} logo/groups ko bhej raha hoon.")
    
    for chat_id in chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=bcast_msg)
            success += 1
            await asyncio.sleep(0.1) 
        except: pass 
            
    await update.message.reply_text(f"✅ Done bhai! {success} jagah message pahunch gaya.")

# ==========================================
# 🛡️ 7. DELETE COMMAND (/d)
# ==========================================
async def delete_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except Exception:
            await update.message.reply_text("Bhai admin power nahi hai mere paas, pehle admin bana group mein!")

# ==========================================
# 🧠 8. AI CHAT (Karan Singh Persona)
# ==========================================
async def chat_with_karan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    
    current_year = datetime.datetime.now().year
    college_year = current_year - 2023 
    
    if user_id not in user_memory: user_memory[user_id] = []
    
    system_prompt = (
        f"You are Karan Singh, a 21-year-old engineering college student from India. "
        f"Your nickname is 'Bright'. CURRENT YEAR: {current_year}. "
        f"You are currently in year {college_year} of your 4-year B.Tech degree. "
        "RULES: 1. Keep responses short (1-2 lines). 2. Talk in natural Hinglish. "
        "3. Be respectful but act like a cool college guy. 4. NEVER act like an AI. "
        "5. If you don't know something, admit it simply."
    )

    user_memory[user_id].append({"role": "user", "content": user_text})
    if len(user_memory[user_id]) > 20: user_memory[user_id].pop(0)

    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
    await asyncio.sleep(1.5)

    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}] + user_memory[user_id]
        )
        reply = response.choices[0].message.content
        user_memory[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except:
        await update.message.reply_text("Yaar abhi busy hoon, baad mein baat karte hain.")

# ==========================================
# 🚀 9. HANDLERS & START
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text("👋 Hey! main Karan hoon. Engineering student. Bol bhai kya chal raha hai?")

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    # 🎯 1. DM Filter: Private chat में कोई कुछ भी बोले (चाहे रिप्लाई या डायरेक्ट), बोट जवाब देगा।
    dm_filter = filters.ChatType.PRIVATE
    
    # 🎯 2. Name Catcher: ग्रुप में अगर कोई 'bright', 'karan' या '@mr_brightbot' लिखेगा, तो ये उसे पकड़ लेगा।
    name_catch = filters.Regex(r'(?i)(\b(bright|karan)\b|@mr_brightbot)')
    
    # 🎯 3. Group Filter: ग्रुप में सिर्फ तभी रिप्लाई करेगा जब -> Reply किया हो, @Tag किया हो, या नाम (name_catch) लिया हो।
    group_filter = filters.ChatType.GROUPS & (filters.REPLY | filters.Entity(constants.MessageEntityType.MENTION) | name_catch)
    
    # 🎯 4. Final Smart Filter: DM और Group दोनों के रूल्स को मिला दिया।
    final_smart_filter = dm_filter | group_filter
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command)) 
    app.add_handler(CommandHandler("bcast", broadcast_message))
    app.add_handler(CommandHandler("d", delete_msg)) 
    
    # यहाँ अपना फाइनल फ़िल्टर लगा दिया
    app.add_handler(MessageHandler(final_smart_filter & filters.TEXT & ~filters.COMMAND, chat_with_karan))
    
    print("✅ Karan (Bright) Live hai (DM = Full Reply, Group = Smart Reply)!")
    app.run_polling()
    
