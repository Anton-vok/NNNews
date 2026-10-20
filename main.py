import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from init_db import init_db
from reg import router as reg_router
from add_post import router as add_router
from help_moderation import router as help_router
import aiosqlite


from match_posts_with_users import match_posts_with_users
from match_users_with_posts import match_users_with_posts
from mailing import send_deliveries, moderation

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GR_ID = os.getenv("ADMIN_CHAT_ID")
if not TOKEN:
    raise RuntimeError("Нет токена в .env")


if init_db() == -1:
    raise RuntimeError("Не удалось создать базу данных")

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(reg_router)
dp.include_router(add_router)
dp.include_router(help_router)

import logging

DB_PATH = "NNNewsDB.sqlite"

async def mailing_loop():
    while True:
        try:
            await asyncio.to_thread(match_posts_with_users, DB_PATH)
            await asyncio.to_thread(match_users_with_posts, DB_PATH)
            async with aiosqlite.connect(DB_PATH) as conn:
                await send_deliveries(conn, bot)
            async with aiosqlite.connect(DB_PATH) as conn:
                await moderation(conn, bot, GR_ID)
        except Exception:
            logging.exception("Ошибка рассылки")   # цикл не должен умирать
        await asyncio.sleep(1)

async def main():
    task = asyncio.create_task(mailing_loop())
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await dp.start_polling(bot, conn=conn)
    finally:
        task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
