import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from init_db import init_db
from reg import router as reg_router
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


async def main():
    async with aiosqlite.connect("NNNewsDB.sqlite") as conn:
        match_posts_with_users("NNNewsDB.sqlite")
        await send_deliveries(conn, bot)

        await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")