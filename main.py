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

# Инициализируем БД перед запуском (если это синхронная функция)
if init_db() == -1:
    raise RuntimeError("Не удалось создать базу данных")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Регистрируем роутеры
dp.include_router(reg_router)


async def main():
    # Открываем асинхронное соединение с БД внутри async-функции через 'async with'
    async with aiosqlite.connect("NNNewsDB.sqlite") as conn:
        # 1. Сначала выполняем логику обработки и рассылки
        match_posts_with_users("NNNewsDB.sqlite")
        await send_deliveries(conn, bot)

        # 2. Запускаем бота. Эта строка «замораживает» выполнение, пока бот работает.
        # Очищаем очередь старых сообщений перед запуском (опционально, но рекомендуется)
        await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
