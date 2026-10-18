from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from parsers import *
import sqlite3
from contextlib import closing



router = Router()

class Form(StatesGroup):
    filling = State()



QUESTIONS = [
    {"key": "title",       "text": "Название?",                     "shift" : 0, "parse": parse_title},
    {"key": "description", "text": "Описание?",                     "shift" : 1},
    {"key": "button_text", "text":"Текст для кнопки",               "shift" : 2,},
    {"key": "button_url",  "text":"Ссылка для кнопки",              "shift" : 0, "parse": parse_url},
    {"key": "location",    "text":"Место проведения",               "shift" : 1,},
    {"key": "starts_at",   "text":"Время проведения",               "shift" : 0, "parse": parse_date},
    {"key": "organizer_id","text":"Выберете ваш тип организации",   "shift" : 0, "options": lambda: db_options("organizations"), "multi": False, "empty_ok": False},
    {"key": "tags",        "text":"Выберете подходящте теги",       "shift" : 0, "options": lambda: db_options("tage"),     "multi": True, "empty_ok": False},
    {"key": "campuses",    "text":"Выберете подходящие кампусы",    "shift" : 0, "options": lambda: db_options("campuses"), "multi": True, "empty_ok": False}
]


def db_options(table):
    with closing(sqlite3.connect("NNNewsDB.sqlite")) as conn:
        return conn.execute(
            f"SELECT id, name FROM {table} ORDER BY name"
        ).fetchall()

def get_options(q):
    opts = q["options"]
    return opts() if callable(opts) else opts


def build_kb(idx, selected=()):
    q = QUESTIONS[idx]
    rows = []
    if q.get("multi"):
        buttons = [
            InlineKeyboardButton(
                text=("✅" if oid in selected else "") + title,
                callback_data=f"tog:{oid}",
            )
            for oid, title in get_options(q)
        ]
        rows += [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        rows.append([InlineKeyboardButton(text="Готово", callback_data="done")])
    elif "options" in q:
        rows.append([
            InlineKeyboardButton(text=title, callback_data=f"ans:{oid}")
            for oid, title in get_options(q)
        ])
    if q["shift"] != 0 and (not q.get("multi")):
        rows.append([InlineKeyboardButton(text="Вперед", callback_data="forward")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def send_question(msg, state, error=""):
    s = await state.get_data()

    if s.get("last_bot_id"):
        await safe_delete(msg.bot, msg.chat.id, s["last_bot_id"])

    idx = s["idx"]
    if idx >= len(QUESTIONS):
        create_post(s["answer"])
        await msg.answer(f"Готово:")
        await state.clear()
        return
    text = QUESTIONS[idx]["text"]
    if error:
        text = f"{error}\n\n{text}"
    send = await msg.answer(text, reply_markup=build_kb(idx))
    await state.update_data(last_bot_id=send.message_id)



async def submit_answer(raw, msg, state):
    s = await state.get_data()
    idx, answer = s["idx"], s["answer"]
    q = QUESTIONS[idx]
    parse = q.get("parse", lambda x:x)

    try:
        value = parse(raw)
    except ValueError as e:
        await send_question(msg, state, error=str(e))
        return

    answer[q["key"]] = value
    await state.update_data(idx=idx+1, answer=answer, selected=[])
    await send_question(msg, state)

async def safe_delete(bot, chat_id, message_id):
    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramBadRequest:
        pass

@router.message(Command("add_post"))
async def add_post(message: Message, state: FSMContext):
    await safe_delete(message.bot, message.chat.id, message.message_id)
    await state.set_state(Form.filling)
    await state.update_data(idx=0, answer={}, selected=[])
    await send_question(message, state)

@router.callback_query(Form.filling, F.data == "forward")
async def forward(callback: CallbackQuery, state: FSMContext):
    s = await state.get_data()
    idx = s["idx"] + QUESTIONS[s["idx"]]["shift"]
    await state.update_data(idx=idx, selected=[])
    await send_question(callback.message, state)
    await callback.answer()


@router.message(Form.filling, F.text)
async def on_text(message: Message, state: FSMContext):
    await safe_delete(message.bot, message.chat.id, message.message_id)
    s = await state.get_data()
    if "options" in QUESTIONS[s["idx"]]:
        return
    await submit_answer(message.text, message, state)

@router.callback_query(Form.filling, F.data.startswith("ans:"))
async def on_button(callback: CallbackQuery, state: FSMContext):
    s = await state.get_data()
    q = QUESTIONS[s["idx"]]
    oid = int(callback.data.split(":")[1])
    if oid not in {o[0] for o in get_options(q)}:
        return await callback.answer()  # такого варианта уже нет
    await submit_answer(oid, callback.message, state)
    await callback.answer()


@router.callback_query(Form.filling, F.data.startswith("tog:"))
async def on_toggle(callback: CallbackQuery, state: FSMContext):
    s = await state.get_data()
    idx = s["idx"]
    if not QUESTIONS[idx].get("multi"):
        return await callback.answer()

    i = int(callback.data.split(":")[1])
    selected = s["selected"]
    if i in selected:
        selected.remove(i)
    else:
        selected.append(i)

    await state.update_data(selected=selected)
    await callback.message.edit_reply_markup(
        reply_markup=build_kb(idx, selected)
    )
    await callback.answer()

@router.callback_query(Form.filling, F.data == "done")
async def on_done(callback: CallbackQuery, state: FSMContext):
    s = await state.get_data()
    q = QUESTIONS[s["idx"]]
    if not q.get("multi"):
        return await callback.answer()

    if not s["selected"] and not q.get("empty_ok"):
        return await callback.answer("Выберете хотя бы один вариант",show_alert=True)

    valid = {oid for oid, _ in get_options(q)}
    values = [i for i in sorted(s["selected"]) if i in valid]
    await submit_answer(values, callback.message, state)

    await callback.answer()

def create_post(answer):
    print(answer)
    with closing(sqlite3.connect("NNNewsDB.sqlite")) as conn:
        cur = conn.execute(
            """INSERT INTO posts (title, description, button_text, button_url,
                   location, starts_at, organizer_id,
                   created_at, moderation_status, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 'approved', 'bot')""",
            (answer["title"], answer.get("description"), answer.get("button_text"),
             answer.get("button_url"), answer.get("location"),
             answer["starts_at"], answer["organizer_id"]),
        )
        post_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO post_campuses (post_id, campus_id) VALUES (?, ?)",
            [(post_id, c) for c in answer["campuses"]])
        conn.executemany(
            "INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)",
            [(post_id, t) for t in answer["tags"]])
        conn.commit()
    return post_id
