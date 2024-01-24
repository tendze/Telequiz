from aiogram.filters.callback_data import CallbackData


class UserRecordsFactory(CallbackData, prefix="user_record"):
    record_id: int
    type_: str
