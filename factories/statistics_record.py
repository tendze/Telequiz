from aiogram.filters.callback_data import CallbackData


class StatisticsRecordsFactory(CallbackData, prefix="statistics_record"):
    id: int
    record_id: int
    session_id: int
    type_: str
