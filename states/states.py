from aiogram.fsm.state import StatesGroup, State


# Состояния во время создания квиза/теста
class CreateQuizOrTestFSM(StatesGroup):
    create_or_cancel_state = State()
    get_time_limit_state = State()


# Состояния главного меню
class MainMenuFSM(StatesGroup):
    q_or_t_list_view = State()  # Состояние просмотра списка созданных квизов/тестов
    q_or_t_view = State()  # Состояние просмотра самих вопросов
    confirmation = State()  # Состояние подтверждения чего-либо


# Состояние во время запуска сессии квиза (для хоста)
class QuizSessionFSM(StatesGroup):
    code_retrieval = State()  # Состояние ожидания ввода кода сессиии
    nickname_retrieval = State()  # Состояние ожидания ввода никнейма
    host_waiting_for_participants = State()  # Состояние ожидания участников (для хоста)
    participant_waiting_for_participants = State()  # Состояне ожидания других участнико (для других участников)
