from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

class HelpStates(StatesGroup):
    waiting_for_message = State()

def setup_help_handlers(group_id):
    
    @router.message(F.text == "/help")
    async def help_command(msg: Message, state: FSMContext):
        await state.set_state(HelpStates.waiting_for_message)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отменить", callback_data="help_cancel")]
        ])
        await msg.answer("Напишите сообщение для администрации:", reply_markup=kb)

    @router.callback_query(F.data == "help_cancel", HelpStates.waiting_for_message)
    async def help_cancel(cb: CallbackQuery, state: FSMContext):
        await state.clear()
        await cb.message.edit_text("Отменено.")
        await cb.answer()

    @router.message(HelpStates.waiting_for_message, F.text)
    async def help_send(msg: Message, state: FSMContext):
        await state.clear()
        user = msg.from_user.username or msg.from_user.id
        
        await msg.bot.send_message(
            chat_id=group_id,
            text=f"📩 От: {user} (ID: {msg.from_user.id})\n\n{msg.text}"
        )
        await msg.answer("Сообщение отправлено администрации.")
