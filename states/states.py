from aiogram.fsm.state import StatesGroup, State


class CreateQuizFSM(StatesGroup):
    get_quiz_name_state = State()
    get_question_state = State()
    get_variants_state = State()
    constructor_menu_state = State()
    edit_variants_state = State()
