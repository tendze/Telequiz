from datetime import date, datetime, time

from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from services.inline_keyboard_services import yes_no_confirmation_row


from aiogram_dialog.widgets.kbd import Calendar, Button
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import (
    Dialog, Window,
)
from dispatcher import dp
from bot import bot
from aiogram_dialog import DialogManager

from states.states import CreateQuizOrTestFSM


async def on_date_selected(cb: CallbackQuery, widget,
                           manager: DialogManager, selected_date: date):
    temp_date = date(selected_date.year, selected_date.month, selected_date.day)
    temp_time = time(23, 59)
    selected_date_time = datetime.combine(temp_date, temp_time)
    time_now = datetime.now()
    if selected_date_time < time_now:
        await cb.answer(text='Дедлайн не может быть раньше сегодняшнего дня')
        return
    await manager.reset_stack()
    await cb.message.delete()
    user_context = dp.fsm.get_context(bot=bot, user_id=cb.from_user.id, chat_id=cb.from_user.id)
    msg = await cb.message.answer(
        text=f'Вы выбрали дедлайн: <b>{selected_date.day}/{selected_date.month}/{selected_date.year} 23:59</b>, верно?',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[yes_no_confirmation_row])
    )
    await user_context.update_data(last_message_id=msg.message_id)
    await user_context.update_data(selected_data=selected_date)
    state_to_switch = (await user_context.get_data()).get('state_to_switch', None)
    if state_to_switch is not None:
        await user_context.set_state(state_to_switch)


calendar = Calendar(id='calendar', on_click=on_date_selected)

calendar_window = Window(
    Const("Выберите дату дедлайна"),
    calendar,
    state=CreateQuizOrTestFSM.get_deadline_state
)
calendar_dialog = Dialog(calendar_window)
