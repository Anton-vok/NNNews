import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
                p.image,
                p.button_text,
                p.button_url,
                p.location,
                p.starts_at
            FROM deliveries d
            JOIN users u ON d.user_id = u.id
            JOIN posts p ON d.post_id = p.id
            WHERE d.sent = 0
            LIMIT 100;
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
            location = task["location"] if task["location"] else ""
            start = task["starts_at"] if task["starts_at"] else ""
            description = task["description"] if task["description"] else ""
            message_text = f"<b>{task['title']}</b>\n\n{location}\n{start}\n{description}"

            reply_markup = None
            if task["button_text"] and task["button_url"]:
                reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=task["button_text"], url=task["button_url"])]
                ])

            try:
                if task["image"]:
                    await bot.send_photo(
                        chat_id=tg_id,
                        photo=task["image"],
                        caption=message_text,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
                else:
                    await bot.send_message(
                        chat_id=tg_id,
                        text=message_text,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )

                await cursor.execute(
                    "UPDATE deliveries SET sent = 1 WHERE id = ?",
                    (delivery_id,)
                )
                logging.info(f"пост {delivery_id} успешно отправлен пользователю {tg_id}.")
            
            except TelegramRetryAfter as e:
                logging.warning(f"Превышен лимит запросов. Повторная попытка через {e.retry_after} секунд.")
                await asyncio.sleep(e.retry_after)
                continue

            except TelegramForbiddenError as e:
                await cursor.execute(
                    "UPDATE deliveries SET sent = -2 WHERE id = ?",
                    (delivery_id,)
                )
                logging.warning(f"Пользователь {tg_id} заблокировал бота. Пост {delivery_id} не будет отправлен.")
            
            except TelegramAPIError as e:
                await cursor.execute(
                    "UPDATE deliveries SET sent = -1 WHERE id = ?",
                    (delivery_id,)
                )
                logging.error(f"Ошибка при отправке поста {delivery_id} пользователю {tg_id}: {e}")

            except Exception as e:
                await cursor.execute(
                    "UPDATE deliveries SET sent = -1 WHERE id = ?",
                    (delivery_id,)
                )
                logging.error(f"Системная ошибка при обработке доставки {delivery_id}: {e}")

            await conn.commit()
            
            await asyncio.sleep(0.05)
