import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
import aiosqlite

async def send_deliveries(conn: aiosqlite.Connection, bot: Bot):
    conn.row_factory = aiosqlite.Row
    async with conn.cursor() as cursor:
        query = """
            SELECT 
                d.id AS delivery_id,
                u.tg_id,
                p.title,
                p.description,
                p.image
            FROM deliveries d
            JOIN users u ON d.user_id = u.id
            JOIN posts p ON d.post_id = p.id
            WHERE d.sent = 0;
        """
        await cursor.execute(query)
        sendings = await cursor.fetchall()

        if not sendings:
            logging.info("План рассылки пуст.")
            return

        logging.info(f"Найдено {len(sendings)} рассылок для отправки.")

        for task in sendings:
            delivery_id = task["delivery_id"]
            tg_id = task["tg_id"]
            
            description = task["description"] if task["description"] else ""
            message_text = f"<b>{task['title']}</b>\n\n{description}"


            try:
                if task["image"]:
                    await bot.send_photo(
                        chat_id=tg_id,
                        photo=task["image"],
                        caption=message_text,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=tg_id,
                        text=message_text,
                        parse_mode="HTML"
                    )

                await cursor.execute(
                    "UPDATE deliveries SET sent = 1 WHERE id = ?",
                    (delivery_id,)
                )
                logging.info(f"пост {delivery_id} успешно отправлен пользователю {tg_id}.")
            
            except TelegramAPIError as e:
                
                await cursor.execute(
                    "UPDATE deliveries SET sent = -1 WHERE id = ?",
                    (delivery_id,)
                )
                logging.error(f"Ошибка при отправке поста {delivery_id} пользователю {tg_id}: {e}")
            
            await asyncio.sleep(0.05)
        
        await conn.commit()


