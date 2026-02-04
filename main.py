from telegram import Update
from telegram.ext import Application, ChatJoinRequestHandler, MessageHandler, filters, ContextTypes

# ---------------- വിവരങ്ങൾ നൽകുക ----------------

BOT_TOKEN = "8563464170:AAFWdI8m-aEVmYtFtSkPyz-QhDH3MWLljf0"

# 1. നിങ്ങളുടെ മെയിൻ ഗ്രൂപ്പ് (ഈ ഗ്രൂപ്പിൽ മാത്രമേ ബോട്ട് നിൽക്കൂ)
# (ഐഡിയുടെ മുന്നിൽ -100 ചേർക്കാൻ മറക്കരുത്)
SOURCE_GROUP_ID = -1002706112246

# 2. ലോഗ് ചാനൽ (ഇതും അനുവദിക്കപ്പെട്ടതാണ്)
LOG_GROUP_ID = -5112941483

# -----------------------------------------------

async def security_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """അനുവാദമില്ലാത്ത ഗ്രൂപ്പിൽ ആരെങ്കിലും ആഡ് ചെയ്താൽ ബോട്ട് ലെഫ്റ്റ് ആകുന്നു"""
    try:
        chat = update.effective_chat
        
        # പ്രൈവറ്റ് ചാറ്റ് ആണെങ്കിൽ കുഴപ്പമില്ല (നിങ്ങൾക്ക് മെസ്സേജ് അയക്കാമല്ലോ)
        if chat.type == "private":
            return

        # നമ്മുടെ ഗ്രൂപ്പോ ലോഗ് ചാനലോ അല്ലെങ്കിൽ ബോട്ട് ലെഫ്റ്റ് ആകും
        if chat.id != SOURCE_GROUP_ID and chat.id != LOG_GROUP_ID:
            await context.bot.send_message(chat_id=chat.id, text="⚠️ This is a Private Bot. I cannot work here. Bye!")
            await context.bot.leave_chat(chat_id=chat.id)
            print(f"Left unauthorized group: {chat.title}")
            
    except Exception as e:
        print(f"Security Error: {e}")

async def auto_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ജോയിൻ റിക്വസ്റ്റ് അപ്രൂവ് ചെയ്യുന്നു (നമ്മുടെ ഗ്രൂപ്പിൽ മാത്രം)"""
    try:
        if update.effective_chat.id == SOURCE_GROUP_ID:
            await context.bot.approve_chat_join_request(chat_id=update.effective_chat.id, user_id=update.effective_user.id)
            
            # ലോഗ് ഗ്രൂപ്പിൽ അറിയിക്കുന്നു
            await context.bot.send_message(
                chat_id=LOG_GROUP_ID, 
                text=f"✅ **JOIN APPROVED**\n👤: {update.effective_user.first_name}"
            )
    except Exception as e:
        print(f"Approve Error: {e}")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """മെസ്സേജ് ലോഗ് ചെയ്യാനും സ്പാം ഡിലീറ്റ് ചെയ്യാനും"""
    try:
        # ആദ്യം സെക്യൂരിറ്റി ചെക്ക് നടത്തുന്നു (അന്യ ഗ്രൂപ്പാണെങ്കിൽ ലെഫ്റ്റ് ആകും)
        if update.effective_chat.id != SOURCE_GROUP_ID:
            await security_check(update, context)
            return

        # --- ഇവിടെ മുതൽ നമ്മുടെ ഗ്രൂപ്പിലെ കാര്യങ്ങൾ ---
        message = update.effective_message
        user = message.from_user
        text = message.text or message.caption or ""

        # 1. SPAM CHECK (Link / Forward)
        is_spam = ("http" in text or "t.me" in text or ".com" in text) or (message.forward_origin is not None)
        
        # അഡ്മിൻ ആണോ എന്ന് നോക്കുന്നു
        chat_admins = await context.bot.get_chat_administrators(SOURCE_GROUP_ID)
        is_admin = user.id in [admin.user.id for admin in chat_admins]

        if is_spam and not is_admin:
            try:
                # Step 1: ലോഗ് ചെയ്യുന്നു
                await context.bot.forward_message(chat_id=LOG_GROUP_ID, from_chat_id=SOURCE_GROUP_ID, message_id=message.message_id)
                await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"🗑️ **SPAM REMOVED**\nUser: {user.first_name}")
                
                # Step 2: ഡിലീറ്റ് ചെയ്യുന്നു
                await message.delete()
                return 
            except:
                pass

        # 2. NORMAL LOGGING (ബാക്കി എല്ലാം ലോഗ് ചെയ്യുന്നു)
        await context.bot.forward_message(chat_id=LOG_GROUP_ID, from_chat_id=SOURCE_GROUP_ID, message_id=message.message_id)

    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Secure Bot Starting...")
    app = Application.builder().token(BOT_TOKEN).build()

    # 1. Join Request
    app.add_handler(ChatJoinRequestHandler(auto_approve))

    # 2. All Messages (Security + Log + Spam)
    app.add_handler(MessageHandler(filters.ALL, handle_everything))

    print("Bot is Running! (Only in YOUR Group)")
    app.run_polling()

if __name__ == "__main__":

    main()
