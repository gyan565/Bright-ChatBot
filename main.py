import os
import random
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, constants, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import ReactionTypeEmoji
from groq import AsyncGroq

# ==========================================
# 🛑 Environment Variables
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BOT_USERNAME = "Mr_Brightbot" 

# ==========================================
# 🌐 Web Server (Back4App Health Check)
# ==========================================
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Mr_Brightbot is Active, Smart, and Stubborn!"

def run_web():
    # Render अपना पोर्ट 'PORT' नाम के वेरिएबल में देता है, अगर नहीं मिला तो 8080 यूज़ करेगा
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# ==========================================
# 🎛️ Menu Setup & Keyboard
# ==========================================
async def post_init(application):
    commands = [
        BotCommand("start", "Bright से बात शुरू करें"),
        BotCommand("help", "हेल्प मेनू देखें")
    ]
    await application.bot.set_my_commands(commands)

def get_bot_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Update Channel", url="https://t.me/Gyan_Expose")],
        [InlineKeyboardButton("➕ Add me in your group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================================
# 🚀 Basic Commands
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "👋 Hey! मैं Bright हूँ。\n\nमुझसे कुछ भी पूछो, मैं तुरंत जवाब दूँगा।\nऔर हाँ, मैं एक असली इंसान हूँ, इसलिए रोबोट मत समझना!\n\nनीचे दिए गए बटन्स का इस्तेमाल करो 👇"
    await update.message.reply_text(text=welcome_text, reply_markup=get_bot_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "🛠️ Bright Bot - Help\n\nमुझसे बात करने के लिए बस अपना मैसेज भेजो! मुझे अपने ग्रुप में ऐड कर लो, मैं वहां भी सबके सवालों के जवाब दूँगा।"
    await update.message.reply_text(text=help_text, reply_markup=get_bot_keyboard())

async def welcome_new_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text("🎉 Hello दोस्तों! मैं Bright हूँ। मुझे ग्रुप में जोड़ने के लिए शुक्रिया, आज से मैं आप सबका दोस्त हूँ!")

# ==========================================
# 🛡️ Admin Group Commands
# ==========================================
async def admin_commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text: return
    if update.message.chat.type not in ['group', 'supergroup']: return
    command = user_text[1:].split()[0].lower()
    
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text("😎 भईया, ये कमांड्स सिर्फ ग्रुप के एडमिन यूज़ कर सकते हैं!")
        return

    reply_msg = update.message.reply_to_message
    if not reply_msg and command != 'unpin':
        await update.message.reply_text("⚠️ इस कमांड को यूज़ करने के लिए यूज़र के किसी मैसेज का रिप्लाई करो।")
        return

    target_user_id = reply_msg.from_user.id if reply_msg else None
    chat_id = update.effective_chat.id

    try:
        if command == 'd':
            await context.bot.delete_message(chat_id=chat_id, message_id=reply_msg.message_id)
            await update.message.delete()
        elif command == 'ban':
            await context.bot.ban_chat_member(chat_id, target_user_id)
            await update.message.reply_text(f"🔨 {reply_msg.from_user.first_name} को ग्रुप से हमेशा के लिए बैन कर दिया गया है!")
        elif command == 'unban':
            await context.bot.unban_chat_member(chat_id, target_user_id, only_if_banned=True)
            await update.message.reply_text(f"✅ {reply_msg.from_user.first_name} को अनबैन कर दिया गया है।")
        elif command == 'kick':
            await context.bot.ban_chat_member(chat_id, target_user_id)
            await context.bot.unban_chat_member(chat_id, target_user_id)
            await update.message.reply_text(f"👢 {reply_msg.from_user.first_name} को ग्रुप से किक कर दिया गया है।")
        elif command == 'mute':
            permissions = ChatPermissions(can_send_messages=False)
            await context.bot.restrict_chat_member(chat_id, target_user_id, permissions)
            await update.message.reply_text(f"🤐 {reply_msg.from_user.first_name} को म्यूट कर दिया गया है।")
        elif command == 'unmute':
            permissions = ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True, can_send_photos=True, can_send_videos=True, can_send_video_notes=True, can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True)
            await context.bot.restrict_chat_member(chat_id, target_user_id, permissions)
            await update.message.reply_text(f"🔊 {reply_msg.from_user.first_name} को अनम्यूट कर दिया गया है।")
        elif command == 'pin':
            await context.bot.pin_chat_message(chat_id, reply_msg.message_id)
        elif command == 'unpin':
            await context.bot.unpin_chat_message(chat_id)
            await update.message.reply_text("📌 मैसेज अनपिन कर दिया गया है।")
    except Exception:
        await update.message.reply_text("❌ मेरे पास एडमिन पावर्स नहीं हैं! पहले मुझे ग्रुप में एडमिन बनाओ।")

# ==========================================
# 🧠 AI Chat (Super Stubborn Retry System)
# ==========================================
async def chat_with_human(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text: return
    if user_text.startswith(('.', '!')): return

    is_group = update.message.chat.type in ['group', 'supergroup']
    is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id

    if is_group:
        if "bright" not in user_text.lower() and not is_reply_to_bot:
            return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    await asyncio.sleep(1.5) 

    user_first_name = update.message.from_user.first_name

    if random.random() < 0.2:
        try:
            emojis = ["👍", "❤️", "😂", "👌", "🔥"]
            await update.message.set_reaction(reaction=ReactionTypeEmoji(random.choice(emojis)))
        except Exception: pass

    system_prompt = (
        f"You are 'Bright'. You are a real, normal human boy living in India. You are strictly NOT an AI, NOT a bot, and NOT a software. "
        f"The user talking to you right now is '{user_first_name}'. "
        f"🛑 STRICT RULES FOR YOUR PERSONA: "
        f"1. GREETING: If the user says 'hi', 'hello', or greets you, reply casually using their name '{user_first_name}'. "
        f"2. DENY BEING A BOT: If the user calls you a bot, AI, or asks about API/software, ACT ANNOYED AND CLUELESS. Say things like: 'Pagal hai kya bhai? Main koi bot nahi hu.', 'Bhai main sacha insaan hu, kya dimag kha raha hai?' "
        f"3. MATH & LOGIC TRICKS: If the user asks you complex math (like 28690+3456789) to 'test' if you are a bot, act like a human. Complain that the math is too hard, or give a slightly wrong answer intentionally, or say 'Ruk bhai calculator nikalne de'. If they catch your mistake, say 'Arre yaar, math thodi weak hai meri, galti insaan se hi hoti hai na, isme bot wali kya baat hai?' "
        f"4. TONE: Speak entirely in natural, casual Hinglish or Hindi. Use words like yaar, bhai, pagle. Never break character."
    )

    # 🔥 3-BAR TRY KARNE WALA LOOP (Retry Logic)
    max_retries = 3
    client = AsyncGroq(api_key=GROQ_API_KEY)

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model="llama3-8b-8192", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ]
            )
            # अगर जवाब मिल गया, तो उसे भेज दो और फंक्शन बंद कर दो
            await update.message.reply_text(response.choices[0].message.content)
            return 
            
        except Exception as e:
            print(f"⚠️ GROQ API ERROR (Attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                # अगर फेल हो गया, तो 2 सेकंड रुको और फिर से ट्राई करो
                await asyncio.sleep(2)
            else:
                # अगर 3 बार में भी जवाब नहीं आया, तब जाकर बहाना मारो
                bahane = [
                    "यार अभी थोड़ा बिजी हूँ, 10 मिनट में मैसेज करता हूँ।",
                    "भाई, मेरा net बहुत स्लो चल रहा है, मैसेज सेंड ही नहीं हो रहा। बाद में बात करते हैं।"
                ]
                await update.message.reply_text(random.choice(bahane))

# ==========================================
# ⚙️ Main Execution
# ==========================================
if __name__ == '__main__':
    print("⏳ Web Server चालू हो रहा है...")
    threading.Thread(target=run_web, daemon=True).start()
    
    print("⏳ Bright ChatBot चालू हो रहा है...")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(MessageHandler(filters.Regex(r"^[.!](ban|unban|kick|mute|unmute|pin|unpin|d)(?:\s|$)"), admin_commands_handler))
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_human))
    
    print("✅ Mr_Brightbot पूरी तरह लाइव है!")
    app.run_polling()
