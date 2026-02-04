import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, ChatJoinRequestHandler, MessageHandler, filters, ContextTypes

# ========================================================
# 👇 1. RENDER SERVER SETTINGS (ഇതാണ് ബോട്ടിനെ ഓഫ് ആക്കാതെ നോക്കുന്നത്)
# ========================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Secure Bot is Running!"

@app.route('/health')
def health():
    return "Healthy", 200

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    print(f"🌍 Web Server starting on port {port}")
    app.run(host='0.0.0.0', port=port)

# ========================================================
# 👇 2. നിങ്ങളുടെ വിവരങ്ങൾ (നിങ്ങൾ തന്ന അതേ കാര്യങ്ങൾ)
# ========================================================

# 1. ബോട്ട് ടോക്കൺ
BOT_TOKEN = "8563464170:AAFWdI8m-aEVmYtFtSkPyz-QhDH3MWLljf0"

# 2. നിങ്ങളുടെ മെയിൻ ഗ്രൂപ്പ് ID
SOURCE_GROUP_ID = -1003621584117

# 3. ലോഗ് ഗ്രൂപ്പ് ID
LOG_GROUP_ID = -5112941483

# ========================================================
# 👇 3. ബോട്ടിന്റെ ഫങ്ക്ഷനുകൾ (നിങ്ങളുടെ കോഡ്)
# ========================================================

async def send_startup_message(application: Application):
    """ബോട്ട് സ്റ്റാർട്ട് ആകുമ്പോൾ ലോഗ് ഗ്രൂപ്പിൽ അറിയിക്കുന്നു"""
    try:
        await application.bot.send_message(chat_id=LOG_GROUP_ID, text="🔒 **Secure Bot is ONLINE!**\nLocked to your Main Group.")
        print("Bot Connected Successfully!")
    except Exception as e:
        print(f"Startup Error: {e}")

async def auto_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ജോയിൻ റിക്വസ്റ്റ് (മെയിൻ ഗ്രൂപ്പിൽ നിന്ന് മാത്രം)"""
    try:
        if update.effective_chat.id != SOURCE_GROUP_ID:
            return

        await context.bot.approve_chat_join_request(chat_id=update.effective_chat.id, user_id=update.effective_user.id)

        # ലോഗ് ഗ്രൂപ്പിൽ അറിയിക്കുന്നു
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"✅ **JOIN APPROVED**\n👤: {update.effective_user.first_name}")
    except Exception as e:
        print(f"Approve Error: {e}")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """സെക്യൂരിറ്റി ചെക്ക്, മെസ്സേജ് കോപ്പി, സ്പാം ഡിലീറ്റ്"""
    try:
        chat = update.effective_chat
        message = update.effective_message

        # 1. പ്രൈവറ്റ് മെസ്സേജ് ആണെങ്കിൽ ഒഴിവാക്കുക
        if chat.type == "private":
            return

        # 2. ലോഗ് ഗ്രൂപ്പിലെ മെസ്സേജ് ആണെങ്കിൽ ഒന്നും ചെയ്യണ്ട
        if chat.id == LOG_GROUP_ID:
            return

        # 🛑 3. SECURITY CHECK
        if chat.id != SOURCE_GROUP_ID:
            try:
                await context.bot.send_message(chat_id=chat.id, text="⚠️ **This is a Private Bot.** I cannot work here. Bye!")
                await context.bot.leave_chat(chat_id=chat.id)
                print(f"Left unauthorized group: {chat.title}")
            except:
                pass
            return

        # --- ഇവിടെ മുതൽ നമ്മുടെ ഗ്രൂപ്പിലെ കാര്യങ്ങൾ ---
        user = message.from_user
        text = (message.text or message.caption or "").lower()

        # A. സ്പാം ചെക്കിംഗ്
        is_link = "http" in text or "t.me" in text or ".com" in text or "www." in text or "@" in text
        is_forward = message.forward_origin is not None

        try:
            chat_admins = await context.bot.get_chat_administrators(chat.id)
            is_admin = user.id in [admin.user.id for admin in chat_admins]
        except:
            is_admin = False

        # സ്പാം ആണെങ്കിൽ (അഡ്മിൻ അല്ലെങ്കിൽ)
        if (is_link or is_forward) and not is_admin:
            try:
                await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"🚨 **SPAM DETECTED** from {user.first_name}")
                await context.bot.copy_message(chat_id=LOG_GROUP_ID, from_chat_id=chat.id, message_id=message.message_id)
                await message.delete()
                return
            except Exception as e:
                print(f"Delete Error: {e}")

        # B. സാധാരണ മെസ്സേജ് ലോഗിങ്ങ്
        try:
            await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"📩 **Msg from:** {user.first_name}")
            await context.bot.copy_message(chat_id=LOG_GROUP_ID, from_chat_id=chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Log Error: {e}")

    except Exception as e:
        print(f"Main Error: {e}")

# ========================================================
# 👇 4. മെയിൻ പ്രോഗ്രാം (ഇവിടെ മാറ്റം വരുത്തി)
# ========================================================

def main():
    # 1. വെബ് സർവർ ബാക്ക്ഗ്രൗണ്ടിൽ സ്റ്റാർട്ട് ചെയ്യുന്നു (Render-ന് വേണ്ടി)
    threading.Thread(target=run_web_server).start()

    print("Secure Bot Starting...")
    app = Application.builder().token(BOT_TOKEN).post_init(send_startup_message).build()
    
    app.add_handler(ChatJoinRequestHandler(auto_approve))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP, handle_everything))
    
    print("Bot is Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
