from aiogram.fsm.state import StatesGroup, State


# Состояния во время создания квиза/теста
class CreateQuizOrTestFSM(StatesGroup):
    get_quiz_or_test_name_state = State()  # Состояние ожидания получения названия квиза/теста
    get_question_state = State()  # Состояние ожидания получения текста вопроса
    get_variants_state = State()  # Состояние ожидания получения вариантов
    constructor_menu_state = State()  # Состояния режима конструктор
    edit_variants_state = State()  # Состояние редактирования


# Состояния главного меню
class MainMenuFSM(StatesGroup):
    q_or_t_view = State()  # Состояние просмотра списка созданных квизов/тестов
