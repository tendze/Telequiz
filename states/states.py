from aiogram.fsm.state import StatesGroup, State


# Состояния во время создания квиза/теста
class CreateQuizOrTestFSM(StatesGroup):
    create_or_cancel_state = State()
    get_time_limit_state = State()


# Состояния главного меню
class MainMenuFSM(StatesGroup):
    q_or_t_view = State()  # Состояние просмотра списка созданных квизов/тестов
