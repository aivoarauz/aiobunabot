import asyncio
import logging
import sys
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_URL, PORT, WEBHOOK_HOST
from database.db import init_db
from handlers import user, admin

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    await init_db()
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
        logger.info(f"Webhook set to {WEBHOOK_URL}")
    else:
        logger.info("No WEBHOOK_HOST — running in polling mode (local)")


async def on_shutdown(bot: Bot):
    if WEBHOOK_URL:
        await bot.delete_webhook()
    logger.info("Bot stopped")


def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN o'rnatilmagan! Environment variable qo'shing.")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(user.router)
    dp.include_router(admin.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if WEBHOOK_HOST:
        # Webhook mode for Render
        app = web.Application()
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        logger.info(f"Starting webhook server on port {PORT}")
        web.run_app(app, host="0.0.0.0", port=PORT)
    else:
        # Polling mode for local testing
        async def run_polling():
            await init_db()
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Starting polling...")
            await dp.start_polling(bot)

        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
def main():
    # Startup va Shutdown hodisalarini ro'yxatdan o'tkazish
    dp.startup.register(on_startup)
    
    app = web.Application()

    # Webhook bo'lsa - Webhook rejimida, bo'lmasa - Polling + Dummy Server rejimida ishlaydi
    if WEBHOOK_HOST:
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=int(PORT))
    else:
        # Gar WEBHOOK kiritilmagan bo'lsa ham Render port xatosisiz polling qilishi uchun:
        async def dummy_handler(request):
            return web.Response(text="Bot runs in Polling mode")
            
        app.router.add_get("/", dummy_handler)
        
        async def run_all():
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", int(PORT))
            await site.start()
            await dp.start_polling(bot)

        asyncio.run(run_all())

if __name__ == "__main__":
    main()
