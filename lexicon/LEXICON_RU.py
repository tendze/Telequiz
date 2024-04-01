LEXICON: dict[str, str] = {
    'greeting': 'Привет, меня зовут Телеквиз бот\nС помощью меня ты можешь создавать квизы и тесты, смотреть '
                'статистику их прохождений',
    'about_bot': 'Данный бот был создан в рамках курсового проекта студентом 2 курса',
    'main_menu': '☰Главное меню',
    'find_session': '🔎Ввести код сессии',
    'create_quiz': '🔨Создать квиз',
    'create_test': '🔨Создать тест',
    'my_profile': '🧑‍💻Мой профиль',
    'my_quizzes': '📕Мои квизы',
    'my_tests': '📘Мои тесты',
    'your_quizzes': 'Ваши квизы📝',
    'your_tests': 'Ваши тесты📝',
    'statistics': '📊Статистика',
    'go_back': '↩Назад',
    'cancel': '❌Отмена',
    'run': '▶️Запустить',
    'edit': '✏️Редактировать',
    'delete_question': '🗑️Удалить вопрос',
    'cancel_edit': '✏️Отменить редактирование',
    'new_question': '➕Новый вопрос',
    'ready': '✅Готово',
    'backward': '<',
    'forward': '>',
    'double_backward': '<<',
    'double_forward': '>>',
    'cross_emoji': '❌',
    'delete': '🗑️Удалить',
    'view': '👀Посмотреть',
    'start': '▶️Начать',
    'send': '📨Отправить',
    'incorrect_code': 'Неккоректный ввод. Введите <b>шестизначное число</b>',
    'code_doesnt_exists': 'Сессии с таким кодом не существует. Введите <b>существующий код</b>.',
    'ask_for_quiz_name': f"<b>Придумайте и отправьте название квиза</b>\n\n"
                         f"В любой момент Вы можете прописать команду "
                         f"<b>/cancel</b> "
                         f" или нажать на кнопку \"❌Отмена\", "
                         "чтобы прекратить создавание квиза, но в таком случае <u>не сохранится</u>",
    'ask_for_test_name': f"<b>Придумайте и отправьте название теста</b>\n\n"
                         f"В любой момент Вы можете прописать команду "
                         f"<b>/cancel</b> "
                         f" или нажать на кнопку \"❌Отмена\", "
                         "чтобы прекратить создавание квиза, но в таком случае данные <u>не сохранятся</u>",
    'choose_time_limit': "Выберите временное ограничение на каждый вопрос",
    'use_my_name': '👤Использовать моё имя',
    'use_my_tag': '🏷️Использовать мой тэг',
    'incorrect_name_30': '<b>Некорректный никнейм.</b>\nНикнейм должен быть непустым и не должен превышать <u>30 '
                         'символов</u>. Также не должно быть знаков препинания.\n'
                         'Введите еще раз ',
    'disconnect': '🔌Отключиться',
    'long_name_error': 'У вас слишком длинное имя.\n'
                       'Введите, пожалуйста, новое!',
    'host_canceled_quiz': '❌<b>Организатор отменил проведение квиза</b>❌',
    'invalid_code': 'Похоже, что организатор отменил проведение квиза.\n'
                    'Введите новый код.',
    'answer': '🔔Ответить',
    'next_question': '➡️Следующий вопрос',
    'finish_quiz': '🔚Завершить квиз',
    'empty_tick': '⬜',
    'tick': '☑',
    'empty_radio': '⚪',
    'radio': '🔘',
    'blocked_answer': '❌Ответить',
    'incorrect_arg_code': '❌Некорректный код подключения',
    'room_is_active': '❌Организатор уже запустил квиз❌',
    'incorrect_link': 'Некорректная ссылка',
    'invalid_link': 'Ссылка неактуальна',
    'pass': '✅Пройти',
    'refuse': '❌Отказаться',
    'yes': '✅Да',
    'no': '❌Нет'
}

LEXICON_COMMANDS: dict[str, str] = {
    '/start': 'Начать работу с ботом',
    '/menu': 'Главное меню',
    '/cancel': 'Прекратить создавание квиза/теста',
    '/about': 'Информация о боте',
}
