from aiogram.filters.callback_data import CallbackData
from database.db_services import Types


class UserRecordsFactory(CallbackData, prefix="user_record"):
    record_id: int
    type_: str
