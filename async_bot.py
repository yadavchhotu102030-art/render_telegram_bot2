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
    filters,
    MessageHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Define configuration constants
URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 8000))
TOKEN = os.environ.get("BOT_TOKEN")

# Validate required environment variables
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Determine mode: webhook if URL is provided, polling otherwise
USE_WEBHOOK = URL is not None
logger.info("Running in %s mode", "webhook" if USE_WEBHOOK else "polling")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    user = update.effective_user
    message = update.message.text if update.message else None

    if not message:
        logger.warning("Received update without text message")
        return

    logger.info("Received message from %s: %s", user.username or user.id, message)
    await update.message.reply_text(message)


async def main() -> None:
    """Set up PTB application and run in webhook or polling mode."""
    if USE_WEBHOOK:
        # Webhook mode for production (Render)
        logger.info("Starting webhook mode with URL: %s", URL)
        application = Application.builder().token(TOKEN).updater(None).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

        # Set webhook
        await application.bot.set_webhook(url=f"{URL}/telegram")

        # Setup web server
        async def telegram(request: Request) -> Response:
            data = await request.json()
            await application.update_queue.put(Update.de_json(data, application.bot))
            return Response()

        async def health(_: Request) -> PlainTextResponse:
            return PlainTextResponse("Bot is running!")

        app = Starlette(
            routes=[
                Route("/telegram", telegram, methods=["POST"]),
                Route("/healthcheck", health, methods=["GET"]),
            ]
        )

        config = uvicorn.Config(app=app, port=PORT, host="0.0.0.0")
        server = uvicorn.Server(config)

        async with application:
            await application.start()
            await server.serve()
            await application.stop()
    else:
        # Polling mode for local development
        logger.info("Starting polling mode for local development")
        application = Application.builder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

        async with application:
            await application.start()
            await application.updater.start_polling()
            logger.info("Bot started! Send a message to test it.")

            # Keep running until interrupted
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
