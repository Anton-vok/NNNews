import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from init_db import init_db
from reg import router as reg_router
from add_post import router as add_router
import aiosqlite

from match_posts_with_users import match_posts_with_users
from mailing import send_deliveries

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Нет токена в .env")


if init_db() == -1:
    raise RuntimeError("Не удалось создать базу данных")

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(reg_router)
dp.include_router(add_router)

import logging

DB_PATH = "NNNewsDB.sqlite"

async def mailing_loop():
    while True:
        try:
            await asyncio.to_thread(match_posts_with_users, DB_PATH)
            async with aiosqlite.connect(DB_PATH) as conn:
                await send_deliveries(conn, bot)
        except Exception:
            logging.exception("Ошибка рассылки")   # цикл не должен умирать
        await asyncio.sleep(30)

async def main():
    task = asyncio.create_task(mailing_loop())
    try:
        await dp.start_polling(bot)
    finally:
        task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
