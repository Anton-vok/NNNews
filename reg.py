import sqlite3
from datetime import date

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

users_data = {}

DEGREES = [("БАК", "BAK"), ("МАГ", "MAG")]

NOTIFY_LABELS = {
    "all": "Да, все",
    "top5": "Да, 5 самых актуальных",
    "none": "Нет",
}


def years():
    today = date.today()
    y = today.year
    if today.month < 9:
        y = y - 1
    result = []
    for i in range(6):
        result.append((str(y - i) + "/" + str(y - i + 1), y - i))
    return result


def get_rows(sql, params=()):
    conn = sqlite3.connect("NNNewsDB.sqlite")
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def make_kb(pairs, prefix, done=None):
    buttons = []
    for label, value in pairs:
        buttons.append([InlineKeyboardButton(text=str(label), callback_data=prefix + ":" + str(value))])
    if done:
        buttons.append([InlineKeyboardButton(text="Готово", callback_data=done)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def start(msg: Message):
    tg_id = msg.from_user.id
    users_data[tg_id] = {"step": "degree"}
    await msg.answer("Вы студент БАК или МАГ?", reply_markup=make_kb(DEGREES, "degree"))


@router.callback_query(F.data.startswith("degree:"))
async def on_degree(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    users_data[tg_id]["degree"] = cb.data.split(":")[1]
    await cb.message.edit_text("В каком году поступили?", reply_markup=make_kb(years(), "year"))
    await cb.answer()


@router.callback_query(F.data.startswith("year:"))
async def on_year(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    users_data[tg_id]["year"] = int(cb.data.split(":")[1])
    rows = get_rows("SELECT id, name FROM campuses")
    pairs = []
    for r in rows:
        pairs.append((r[1], r[0]))
    await cb.message.edit_text("Ваш кампус?", reply_markup=make_kb(pairs, "campus"))
    await cb.answer()


@router.callback_query(F.data.startswith("campus:"))
async def on_campus(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    campus_id = int(cb.data.split(":")[1])
    users_data[tg_id]["campus_id"] = campus_id
    rows = get_rows("SELECT id, name FROM faculties WHERE campus_id = ?", (campus_id,))
    pairs = []
    for r in rows:
        pairs.append((r[1], r[0]))
    await cb.message.edit_text("Ваш факультет?", reply_markup=make_kb(pairs, "faculty"))
    await cb.answer()


@router.callback_query(F.data.startswith("faculty:"))
async def on_faculty(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    faculty_id = int(cb.data.split(":")[1])
    users_data[tg_id]["faculty_id"] = faculty_id
    rows = get_rows("SELECT id, name FROM programs WHERE faculty_id = ?", (faculty_id,))
    pairs = []
    for r in rows:
        pairs.append((r[1], r[0]))
    await cb.message.edit_text("Ваша ОП?", reply_markup=make_kb(pairs, "program"))
    await cb.answer()


@router.callback_query(F.data.startswith("program:"))
async def on_program(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    users_data[tg_id]["program_id"] = int(cb.data.split(":")[1])
    users_data[tg_id]["tags"] = []
    rows = get_rows("SELECT id, name FROM tage")
    pairs = []
    for r in rows:
        pairs.append(("⬜ " + r[1], r[0]))
    await cb.message.edit_text("Выберите теги:", reply_markup=make_kb(pairs, "tag", "tags_done"))
    await cb.answer()


@router.callback_query(F.data.startswith("tag:"))
async def on_tag(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    tag_id = int(cb.data.split(":")[1])
    if tag_id in users_data[tg_id]["tags"]:
        users_data[tg_id]["tags"].remove(tag_id)
    else:
        users_data[tg_id]["tags"].append(tag_id)
    rows = get_rows("SELECT id, name FROM tage")
    pairs = []
    for r in rows:
        if r[0] in users_data[tg_id]["tags"]:
            pairs.append(("✅ " + r[1], r[0]))
        else:
            pairs.append(("⬜ " + r[1], r[0]))
    await cb.message.edit_reply_markup(reply_markup=make_kb(pairs, "tag", "tags_done"))
    await cb.answer()


@router.callback_query(F.data == "tags_done")
async def on_tags_done(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    users_data[tg_id]["orgs"] = []
    rows = get_rows("SELECT id, name FROM organizations")
    pairs = []
    for r in rows:
        pairs.append(("⬜ " + r[1], r[0]))
    await cb.message.edit_text("Где участвуете?", reply_markup=make_kb(pairs, "org", "orgs_done"))
    await cb.answer()


@router.callback_query(F.data.startswith("org:"))
async def on_org(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    org_id = int(cb.data.split(":")[1])
    if org_id in users_data[tg_id]["orgs"]:
        users_data[tg_id]["orgs"].remove(org_id)
    else:
        users_data[tg_id]["orgs"].append(org_id)
    rows = get_rows("SELECT id, name FROM organizations")
    pairs = []
    for r in rows:
        if r[0] in users_data[tg_id]["orgs"]:
            pairs.append(("✅ " + r[1], r[0]))
        else:
            pairs.append(("⬜ " + r[1], r[0]))
    await cb.message.edit_reply_markup(reply_markup=make_kb(pairs, "org", "orgs_done"))
    await cb.answer()


@router.callback_query(F.data == "orgs_done")
async def on_orgs_done(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return
    notify_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, все", callback_data="notify:all")],
        [InlineKeyboardButton(text="Да, 5 самых актуальных", callback_data="notify:top5")],
        [InlineKeyboardButton(text="Нет", callback_data="notify:none")],
    ])
    await cb.message.edit_text("Хотите получать анонсы?", reply_markup=notify_kb)
    await cb.answer()


@router.callback_query(F.data.startswith("notify:"))
async def on_notify(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if tg_id not in users_data:
        await cb.answer("Начните с /start")
        return

    users_data[tg_id]["notify"] = cb.data.split(":")[1]
    d = users_data[tg_id]

    conn = sqlite3.connect("NNNewsDB.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
    row = cur.fetchone()

    if row is None:
        cur.execute(
            "INSERT INTO users (tg_id, admission_year, program_id, degree, faculty_id, campus_id) VALUES (?, ?, ?, ?, ?, ?)",
            (tg_id, d["year"], d["program_id"], d["degree"], d["faculty_id"], d["campus_id"])
        )
        cur.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        user_id = cur.fetchone()[0]
    else:
        user_id = row[0]
        cur.execute(
            "UPDATE users SET admission_year = ?, program_id = ?, degree = ?, faculty_id = ?, campus_id = ? WHERE tg_id = ?",
            (d["year"], d["program_id"], d["degree"], d["faculty_id"], d["campus_id"], tg_id)
        )

    cur.execute("DELETE FROM user_tags WHERE user_id = ?", (user_id,))
    for tag_id in d["tags"]:
        cur.execute("INSERT INTO user_tags (user_id, tag_id) VALUES (?, ?)", (user_id, tag_id))

    cur.execute("DELETE FROM user_orgs WHERE user_id = ?", (user_id,))
    for org_id in d["orgs"]:
        cur.execute("INSERT INTO user_orgs (user_id, org_id) VALUES (?, ?)", (user_id, org_id))

    conn.commit()
    conn.close()

    await cb.message.edit_text(
        "Готово! Ваш ID: " + str(user_id) +
        "\nАнонсы: " + NOTIFY_LABELS[d["notify"]]
    )
    await cb.answer()