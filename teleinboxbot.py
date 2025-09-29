import logging, json, os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters
)

# === KONFIGURASI ===
BOT_TOKEN = "23423:jbehHhaehaeaffasefssef" # ganti dengan bot token kamu
ADMIN_ID  = 123456789 # ganti dengan user admin telegram kamu
BLOCK_FILE = "blocked.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def load_blocked():
    if os.path.exists(BLOCK_FILE):
        with open(BLOCK_FILE) as f:
            return set(json.load(f))
    return set()

def save_blocked():
    with open(BLOCK_FILE, "w") as f:
        json.dump(list(BLOCKED_USERS), f)

BLOCKED_USERS = load_blocked()

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = user.id
    if chat_id in BLOCKED_USERS:
        return
    text = update.message.text or "<no text>"
    info = (
        f"💬 Pesan baru dari user:\n"
        f"🆔 User ID: {chat_id}\n"
        f"👤 Nama: {user.full_name}\n"
        f"🔗 Username: @{user.username if user.username else '—'}\n"
        f"---\n{text}"
    )
    if update.message.photo:
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=info)
    elif update.message.video:
        await context.bot.send_video(ADMIN_ID, update.message.video.file_id, caption=info)
    elif update.message.document:
        await context.bot.send_document(ADMIN_ID, update.message.document.file_id, caption=info)
    else:
        await context.bot.send_message(ADMIN_ID, text=info)

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not update.message.reply_to_message:
        return
    lines = (update.message.reply_to_message.caption.splitlines()
             if update.message.reply_to_message.caption
             else update.message.reply_to_message.text.splitlines())
    buyer_id = None
    for line in lines:
        if line.startswith("🆔 User ID:"):
            buyer_id = line.split(":")[1].strip()
            break
    if not buyer_id:
        return
    target = int(buyer_id)
    if update.message.photo:
        await context.bot.send_photo(target, update.message.photo[-1].file_id,
                                     caption=update.message.caption or "")
    elif update.message.video:
        await context.bot.send_video(target, update.message.video.file_id,
                                     caption=update.message.caption or "")
    elif update.message.document:
        await context.bot.send_document(target, update.message.document.file_id,
                                        caption=update.message.caption or "")
    elif update.message.text:
        await context.bot.send_message(target, text=update.message.text)

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Gunakan: /block <user_id>")
        return
    uid = int(context.args[0])
    BLOCKED_USERS.add(uid)
    save_blocked()
    await update.message.reply_text(f"User {uid} telah diblokir.")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Gunakan: /unblock <user_id>")
        return
    uid = int(context.args[0])
    BLOCKED_USERS.discard(uid)
    save_blocked()
    await update.message.reply_text(f"User {uid} telah di-unblock.")

async def list_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fitur = (
        "<b>🤖 Daftar Fitur Bot</b>\n\n"
        "• /block &lt;user_id&gt; – blokir user\n"
        "• /unblock &lt;user_id&gt; – buka blokir user\n"
        "• /help atau /fitur – menampilkan daftar fitur ini\n"
    )
    await update.message.reply_text(fitur, parse_mode="HTML")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE
        & ~filters.User(user_id=ADMIN_ID)
        & (filters.TEXT | filters.PHOTO | filters.VIDEO
           | filters.Sticker.ALL | filters.VOICE | filters.Document.ALL),
        forward_to_admin
    ))
    app.add_handler(MessageHandler(
        filters.REPLY & filters.User(user_id=ADMIN_ID)
        & (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL),
        admin_reply
    ))
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CommandHandler("unblock", unblock_user))
    app.add_handler(CommandHandler(["help", "fitur"], list_features))
    print("Bot aktif. Tekan Ctrl+C untuk berhenti.")
    app.run_polling()

if __name__ == "__main__":
    main()
