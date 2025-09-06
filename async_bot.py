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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Configuration
URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 8000))
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

USE_WEBHOOK = URL is not None
logger.info("Running in %s mode", "webhook" if USE_WEBHOOK else "polling")

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Welcome to Anonymous Chat Bot!\nType /chat to find a partner.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Available commands:\n/start\n/help\n/chat\n/leave")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Looking for a chat partner... (This is just a placeholder.)")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text if update.message else None
    if message:
        await update.message.reply_text(message)

# Main logic
async def main() -> None:
    application = Application.builder().token(TOKEN).updater(None).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("chat", chat))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    if USE_WEBHOOK:
        await application.bot.set_webhook(url=f"{URL}/telegram")

        async def telegram(request: Request) -> Response:
            data = await request.json()
            await application.update_queue.put(Update.de_json(data, application.bot))
            return Response()

        async def health(_: Request) -> PlainTextResponse:
            return PlainTextResponse("Bot is running!")

        app = Starlette(routes=[
            Route("/telegram", telegram, methods=["POST"]),
            Route("/healthcheck", health, methods=["GET"]),
        ])

        config = uvicorn.Config(app=app, port=PORT, host="0.0.0.0")
        server = uvicorn.Server(config)

        async with application:
            await application.start()
            await server.serve()
            await application.stop()
    else:
        async with application:
            await application.start()
            await application.updater.start_polling()
            logger.info("Bot started! Send a message to test it.")

            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass
            finally:
                await application.updater.stop()
                await application.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot failed to start: %s", e)
        raise
        
