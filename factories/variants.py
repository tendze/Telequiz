from aiogram.filters.callback_data import CallbackData


class VariantsFactory(CallbackData, prefix="variants"):
    var_number: int
