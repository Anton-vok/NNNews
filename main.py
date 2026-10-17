import os
import asyncio

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from init_db import init_db
from reg import router as reg_router

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Нет токена в .env")

if init_db() == -1:
    raise RuntimeError("Не удалось создать базу данных")

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    dp.include_router(reg_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
