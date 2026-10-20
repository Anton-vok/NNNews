import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from datetime import datetime

async def send_deliveries(conn: aiosqlite.Connection, bot: Bot):
    conn.row_factory = aiosqlite.Row
    async with conn.cursor() as cursor:
        query = """
            SELECT 
                p.id AS post_id,
                d.id AS delivery_id,
                u.tg_id,
                p.title,
                p.description,
                p.image,
                p.button_text,
                p.button_url,
                p.location,
                p.starts_at,
                d.mail_date
            FROM deliveries d
            JOIN users u ON d.user_id = u.id
            JOIN posts p ON d.post_id = p.id
            WHERE d.sent = 0 AND d.mail_date <= datetime('now', 'localtime')
            LIMIT 100;
        """
        await cursor.execute(query)
        sendings = await cursor.fetchall()

        if not sendings:
            logging.info("План рассылки пуст.")
            return

        logging.info(f"Найдено {len(sendings)} рассылок для отправки.")

        for task in sendings:
            now = datetime.now()
            date = datetime.strptime(task["mail_date"], "%Y-%m-%d %H:%M:%S")

            if now < date:
                continue

            delivery_id = task["delivery_id"]
            tg_id = task["tg_id"]
            location = task["location"] if task["location"] else ""
            start = task["starts_at"] if task["starts_at"] else ""
            description = task["description"] if task["description"] else ""
            hi_message = "Добавлено новое мероприятие"
            message_text = f"+{hi_message}\n\n<b>{task['title']}</b>\n\n{description}\n\n📍 {location}\n⏰ {start}"

            inline_keyboard = []
            if task["button_text"] and task["button_url"]:
                inline_keyboard.append([InlineKeyboardButton(text=task["button_text"], url=task["button_url"])])

            inline_keyboard.append([InlineKeyboardButton(text="🔔 Напомнить мне", callback_data=f"remind:{task['post_id'] or delivery_id}")])
            reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

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

                await conn.execute(
                    "UPDATE deliveries SET sent = 1 WHERE id = ?",
                    (delivery_id,)
                )
                logging.info(f"пост {delivery_id} успешно отправлен пользователю {tg_id}.")
        
            except TelegramRetryAfter as e:
                logging.warning(f"Превышен лимит запросов. Повторная попытка через {e.retry_after} секунд.")
                await asyncio.sleep(e.retry_after)
                break

            except TelegramForbiddenError as e:
                await conn.execute(
                    "UPDATE deliveries SET sent = -2 WHERE id = ?",
                    (delivery_id,)
                )
                logging.warning(f"Пользователь {tg_id} заблокировал бота. Пост {delivery_id} не будет отправлен.")
        
            except TelegramAPIError as e:
                await conn.execute(
                    "UPDATE deliveries SET sent = -1 WHERE id = ?",
                    (delivery_id,)
                )
                logging.error(f"Ошибка при отправке поста {delivery_id} пользователю {tg_id}: {e}")

            except Exception as e:
                await conn.execute(
                    "UPDATE deliveries SET sent = -1 WHERE id = ?",
                    (delivery_id,)
                )
                logging.error(f"Системная ошибка при обработке доставки {delivery_id}: {e}")

            await conn.commit()
        
            await asyncio.sleep(0.05)


async def moderation(conn: aiosqlite.Connection, bot: Bot, moder_chat):
    conn.row_factory = aiosqlite.Row
    async with conn.cursor() as cursor:
        query = """
            SELECT
                p.title,
                p.image,
                p.description,
                p.button_text,
                p.button_url,
                p.location,
                p.starts_at,
                p.id
            FROM posts p
            WHERE p.moderation_status = 'pending'
        """

        await cursor.execute(query)

        moderate = await cursor.fetchall()

        if not moderate:
            logging.info("Нет постов для модерации.")
            return

        for task in moderate:
            description = task["description"] if task["description"] else ""
            location = task["location"] if task["location"] else ""
            start = task["starts_at"] if task["starts_at"] else ""
            hi_message = "Добавлено новое мероприятие"

            message_text = f"+{hi_message}\n\n<b>{task['title']}</b>\n\n{description}\n\n📍 {location}\n⏰ {start}"

            inline_keyboard = []
            if task["button_text"] and task["button_url"]:
                inline_keyboard.append([InlineKeyboardButton(text=task["button_text"], url=task["button_url"])])

            inline_keyboard.append([
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"mod:approved:{task['id']}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"mod:rejected:{task['id']}")
            ])

            reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

            try:
                if task["image"]:
                    await bot.send_photo(
                        chat_id=moder_chat,
                        photo=task["image"],
                        caption=message_text,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
                else:
                    await bot.send_message(
                        chat_id=moder_chat,
                        text=message_text,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )

                await conn.execute(
                    "UPDATE posts SET moderation_status = 'moderation' WHERE id = ?",
                    (task["id"],)
                )
                logging.info(f"пост {task['id']} успешно отправлен на модерацию.")

            except Exception as e:
                logging.error(f"Ошибка при отправке поста {task['id']} на модерацию: {e}")

            await conn.commit()


async def send_reminders(conn: aiosqlite.Connection, bot: Bot):
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
            WHERE d.resend = 1 AND datetime(date(p.starts_at) || ' 08:00:00') <= datetime('now', 'localtime')
            LIMIT 100;
        """

        await cursor.execute(query)
        reminders = await cursor.fetchall()

        if not reminders:
            return

        logging.info(f"Найдено {len(reminders)} напоминаний для отправки на 08:00 утра.")

        for task in reminders:
            delivery_id = task["delivery_id"]
            tg_id = task["tg_id"]
            location = task["location"] if task["location"] else ""
            start = task["starts_at"] if task["starts_at"] else ""
            description = task["description"] if task["description"] else ""
            
            message_text = f"⏰ <b>НАПОМИНАНИЕ О МЕРОПРИЯТИИ СЕГОДНЯ!</b>\n\n<b>{task['title']}</b>\n\n{description}\n\n📍 {location}\n⏰ {start}"

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

                await conn.execute("UPDATE deliveries SET resend = 2 WHERE id = ?", (delivery_id,))
                logging.info(f"Напоминание по доставке {delivery_id} успешно отправлено пользователю {tg_id}.")
        
            except TelegramForbiddenError:
                await conn.execute("UPDATE deliveries SET resend = -2 WHERE id = ?", (delivery_id,))
            except TelegramAPIError as e:
                await conn.execute("UPDATE deliveries SET resend = -1 WHERE id = ?", (delivery_id,))
                logging.error(f"Ошибка API при отправке напоминания по доставке {delivery_id}: {e}")
            except Exception as e:
                await conn.execute("UPDATE deliveries SET resend = -1 WHERE id = ?", (delivery_id,))
                logging.error(f"Системная ошибка в напоминании по доставке {delivery_id}: {e}")

            await conn.commit()
            await asyncio.sleep(0.05)
