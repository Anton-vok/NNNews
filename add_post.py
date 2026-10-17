import sqlite3
from datetime import date

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("add_post"))
async def add_post(msg: Message):



# def make_kb(pairs, prefix, done=None):
#     buttons = []
#     for label, value in pairs:
#         buttons.append([InlineKeyboardButton(text=str(label), callback_data=prefix + ":" + str(value))])
#     if done:
#         buttons.append([InlineKeyboardButton(text="Готово", callback_data=done)])
#     return InlineKeyboardMarkup(inline_keyboard=buttons)
#
#
# @router.message(Command("addPost"))
# async def start(msg: Message):
#     tg_id = msg.from_user.id
#     users_data[tg_id] = {"step": "degree"}
#     await msg.answer("Вы студент БАК или МАГ?", reply_markup=make_kb(DEGREES, "degree"))
#
#
# @router.callback_query(F.data.startswith("degree:"))
# async def on_degree(cb: CallbackQuery):
#     tg_id = cb.from_user.id
#     if tg_id not in users_data:
#         await cb.answer("Начните с /start")
#         return
#     users_data[tg_id]["degree"] = cb.data.split(":")[1]
#     await cb.message.edit_text("В каком году поступили?", reply_markup=make_kb(years(), "year"))
#     await cb.answer()

