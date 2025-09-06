import asyncio
import logging
import os

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 8000))
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

USE_WEBHOOK = URL is not None

# Global in-memory chat state
waiting_users = []
active_chats = {}

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to Anonymous Chat Bot!\nType /chat to find a partner.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n/start - Start bot\n/chat - Find a partner\n/leave - Leave chat\n/help - Show help")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        await update.message.reply_text("❗ You are already in a chat. Type /leave to end it.")
        return

    if user_id in waiting_users:
        await update.message.reply_text("⏳ You are already in the queue. Please wait...")
        return

    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await context.bot.send_message(partner_id, "✅ You are now connected! Say hi 👋")
        await update.message.reply_text("✅ You are now connected! Say hi 👋")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("⏳ Waiting for a partner to connect...")

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)

        await context.bot.send_message(partner_id, "❌ Your partner left the chat.")
        await update.message.reply_text("❌ You left the chat.")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        await update.message.reply_text("❌ You left the waiting queue.")
    else:
        await update.message.reply_text("❗ You are not in a chat or queue.")

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        if update.message.text:
            await context.bot.send_message(partner_id, update.message.text)
        elif update.message.sticker:
            await context.bot.send_sticker(partner_id, update.message.sticker.file_id)
        elif update.message.photo:
            await context.bot.send_photo(partner_id, update.message.photo[-1].file_id)
        elif update.message.document:
            await context.bot.send_document(partner_id, update.message.document.file_id)
    else:
        await update.message.reply_text("❗ You are not in a chat. Type /chat to find a partner.")

# Main bot runner
async def main():
    app = Application.builder().token(TOKEN).updater(None).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chat", chat))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(MessageHandler(filters.TEXT | filters.Sticker | filters.PHOTO | filters.Document, forward_message))

    if USE_WEBHOOK:
        await app.bot.set_webhook(url=f"{URL}/telegram")

        async def telegram(request: Request) -> Response:
            data = await request.json()
            await app.update_queue.put(Update.de_json(data, app.bot))
            return Response()

        async def health(_: Request) -> PlainTextResponse:
            return PlainTextResponse("Bot is running!")

        star_app = Starlette(routes=[
            Route("/telegram", telegram, methods=["POST"]),
            Route("/healthcheck", health, methods=["GET"]),
        ])

        config = uvicorn.Config(app=star_app, port=PORT, host="0.0.0.0")
        server = uvicorn.Server(config)

        async with app:
            await app.start()
            await server.serve()
            await app.stop()
    else:
        async with app:
            await app.start()
            await app.updater.start_polling()
            await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error("Error: %s", e)
        raise
        
