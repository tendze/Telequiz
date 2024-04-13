import pymysql as mysql
from .config import mysql_db_name, mysql_db_username, mysql_db_password, mysql_host, mysql_port
from classes.question import Question
from enum import Enum
from encrypting.question_encripting import encrypt_text, decrypt_bytes
from collections import defaultdict


# Служебный класс, представляющий квиз/тест
class RecordTypes(Enum):
    Quiz = 'Q'
    Test = 'T'


# Служебный ласс, представляющий статус сессии квиза
class QuizStatus(Enum):
    Waiting = 'Waiting'
    InProcess = 'InProcess'
    Finished = 'Finished'


# Получение соединения с БД
def db_connection(db_name: str | None = None):
    connection = mysql.connect(
        host=mysql_host,
        port=int(mysql_port),
        user=mysql_db_username,
        password=mysql_db_password,
        database=db_name,
        cursorclass=mysql.cursors.DictCursor
    )
    return connection


# Инициализация БД
async def initialize_db():
    conn = db_connection()
    with conn:
        with conn.cursor() as cursor:
            create_db_query = "CREATE DATABASE IF NOT EXISTS {db_name}".format(db_name=mysql_db_name)
            use_db_query = "USE {db_name}".format(db_name=mysql_db_name)
            cursor.execute(create_db_query)
            cursor.execute(use_db_query)
            create_users_table_query = "CREATE TABLE IF NOT EXISTS User(" \
                                       "record_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT," \
                                       "tg_id BIGINT UNSIGNED NOT NULL," \
                                       "name VARCHAR(100)," \
                                       "type ENUM('Q', 'T')," \
                                       "time_limit INT UNSIGNED," \
                                       "deadline VARCHAR(100)" \
                                       ")"
            create_questions_table_query = "CREATE TABLE IF NOT EXISTS Question(" \
                                           "id INT UNSIGNED," \
                                           "FOREIGN KEY (id) REFERENCES User(record_id)," \
                                           "question_text VARCHAR(100)," \
                                           "variants_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT," \
                                           "consider_partial_answers bit" \
                                           ")"
            create_variants_table_query = "CREATE TABLE IF NOT EXISTS Variant(" \
                                          "id INT UNSIGNED," \
                                          "FOREIGN KEY (id) REFERENCES Question(variants_id)," \
                                          "variant_text VARCHAR(30)" \
                                          ")"
            create_right_variants_table_query = "CREATE TABLE IF NOT EXISTS Right_variant(" \
                                                "id INT UNSIGNED," \
                                                "FOREIGN KEY (id) REFERENCES Question(variants_id)," \
                                                "encrypted_text VARCHAR(228)" \
                                                ")"
            create_quiz_host_session_table_query = "CREATE TABLE IF NOT EXISTS Quiz_host_session(" \
                                                   "id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT," \
                                                   "code INT NOT NULL," \
                                                   "user_host_id BIGINT UNSIGNED NOT NULL," \
                                                   "quiz_record_id INT UNSIGNED," \
                                                   "start_time VARCHAR(100)" \
                                                   ")"
            create_quiz_participant_session_table_query = "CREATE TABLE IF NOT EXISTS Quiz_participant_session(" \
                                                          "id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT," \
                                                          "quiz_session_id INT UNSIGNED," \
                                                          "FOREIGN KEY (quiz_session_id) REFERENCES " \
                                                          "Quiz_host_session(id)," \
                                                          "code INT NOT NULL," \
                                                          "user_participant_id BIGINT UNSIGNED NOT NULL" \
                                                          ")"
            create_quiz_statistics_table_query = "CREATE TABLE IF NOT EXISTS Quiz_statistics(" \
                                                 "id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT," \
                                                 "tg_id BIGINT UNSIGNED NOT NULL," \
                                                 "host_tg_id BIGINT UNSIGNED NOT NULL," \
                                                 "record_id INT UNSIGNED," \
                                                 "nickname VARCHAR(30)," \
                                                 "record_name VARCHAR(100)," \
                                                 "score DOUBLE," \
                                                 "max_score TINYINT UNSIGNED," \
                                                 "start_time VARCHAR(100)," \
                                                 "session_id INT UNSIGNED" \
                                                 ")"
            create_test_statistics_table_query = "CREATE TABLE IF NOT EXISTS Test_statistics(" \
                                                 "id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT," \
                                                 "tg_id BIGINT UNSIGNED NOT NULL," \
                                                 "host_tg_id BIGINT UNSIGNED NOT NULL," \
                                                 "record_id INT UNSIGNED," \
                                                 "nickname VARCHAR(129)," \
                                                 "record_name VARCHAR(100)," \
                                                 "score DOUBLE," \
                                                 "max_score TINYINT UNSIGNED," \
                                                 "start_time VARCHAR(100)" \
                                                 ")"
            cursor.execute(create_users_table_query)
            cursor.execute(create_questions_table_query)
            cursor.execute(create_variants_table_query)
            cursor.execute(create_right_variants_table_query)
            cursor.execute(create_quiz_host_session_table_query)
            cursor.execute(create_quiz_participant_session_table_query)
            cursor.execute(create_quiz_statistics_table_query)
            cursor.execute(create_test_statistics_table_query)


# Вставляет данные после в таблицы User, Question, Variant и Right_variant
async def insert_questions(user_tg_id: int,
                           name: str,
                           questions: list[Question],
                           type_: RecordTypes,
                           quiz_timer: int = 0,
                           deadline: str = None):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO User(tg_id, name, type, time_limit, deadline) VALUES(%s, %s, %s, %s, %s)",
                           (user_tg_id, name, type_.value, None if quiz_timer == 0 else quiz_timer, deadline))
            conn.commit()

            last_user_record_id = await get_last_inserted_id(table="User", cursor=cursor)

            for question in questions:
                cursor.execute("INSERT INTO Question(id, question_text, consider_partial_answers) VALUES(%s, %s, %s)",
                               (last_user_record_id, question.question,
                                1 if question.consider_partial_answers == 1 else 0))
                conn.commit()
                cursor.execute("SELECT LAST_INSERT_ID() FROM Question")
                last_variant_id = cursor.fetchone()['LAST_INSERT_ID()']
                for variant in question.variants:
                    cursor.execute("INSERT INTO Variant(id, variant_text) VALUES(%s, %s)", (last_variant_id, variant))
                for right_variant in question.right_variants:
                    encrypted_variant = encrypt_text(right_variant)
                    cursor.execute("INSERT INTO Right_variant(id, encrypted_text) VALUES(%s, %s)",
                                   (last_variant_id, encrypted_variant))
                conn.commit()


# Возващает словарь вида record_id: name, где record_id - айди записи, а name - название квиза/теста
async def get_user_record_names(tg_id: int, type_: RecordTypes) -> dict[int, str]:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT record_id, name FROM User WHERE tg_id = %s AND type = %s", (tg_id, type_.value))
            user_q_or_t_id = cursor.fetchall()
            return user_q_or_t_id


# Получить все записи пользователя по айди
async def get_user_record_questions(
        record_id: int,
) -> list[Question]:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT question_text, variants_id, consider_partial_answers FROM question WHERE id = %s",
                           record_id)
            rows = cursor.fetchall()
            questions: list[Question] = []
            for data in rows:
                variants_id = data['variants_id']
                cursor.execute("SELECT variant_text FROM variant WHERE id = %s", variants_id)
                data['variants'] = [variant['variant_text'] for variant in cursor.fetchall()]
                cursor.execute("SELECT encrypted_text FROM right_variant WHERE id = %s", variants_id)
                data['right_variants'] = [decrypt_bytes(right_variant['encrypted_text'].encode())
                                          for right_variant in cursor.fetchall()]
                questions.append(
                    Question(
                        question=data['question_text'],
                        variants=data['variants'],
                        right_variants=data['right_variants'],
                        consider_partial_answers=True if int.from_bytes(
                            data['consider_partial_answers'],
                            byteorder='little') == 1
                        else False
                    )
                )
            return questions


# Получает ограничение по времени записи
async def get_time_limit(record_id) -> int | None:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM User WHERE record_id = %s", record_id)
            return cursor.fetchone()['time_limit']


# Удалить запись
async def delete_user_record(record_id: int) -> None:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT variants_id FROM question WHERE id = %s', record_id)
            to_delete_data = cursor.fetchall()
            for data in to_delete_data:
                variant_id = data['variants_id']
                cursor.execute('DELETE FROM variant WHERE id = %s', variant_id)
                conn.commit()
                cursor.execute('DELETE FROM right_variant WHERE id = %s', variant_id)
                conn.commit()
            cursor.execute('DELETE FROM question WHERE id = %s', record_id)
            conn.commit()
            cursor.execute('DELETE FROM user WHERE record_id = %s', record_id)
            conn.commit()


# Добавить код сессии
async def insert_code(
        code: int,
        user_id: int,
        quiz_record_id: int,
        time: str
) -> int:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO Quiz_host_session(code, user_host_id, quiz_record_id, "
                           "start_time) "
                           " VALUES(%s, %s, %s, %s)",
                           (code, user_id, quiz_record_id, time))
            conn.commit()
            last_id = await get_last_inserted_id(table="Quiz_host_session", cursor=cursor)
            return last_id


# Добавить нового участника
async def insert_participant(
        quiz_session_id: int,
        code: int,
        user_participant_id: int
):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO Quiz_participant_session(quiz_session_id, code, user_participant_id) "
                           "VALUES(%s, %s, %s)",
                           (quiz_session_id, code, user_participant_id))
            conn.commit()


# Удалить сессию по коду
async def delete_code(record_id) -> None:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Quiz_participant_session WHERE quiz_session_id = %s", record_id)
            conn.commit()
            cursor.execute("DELETE FROM Quiz_host_session WHERE id = %s", record_id)
            conn.commit()


# Удаляет участника из БД по id пользователя (или же id чата с пользователем)
async def delete_participant(tg_id) -> None:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Quiz_participant_session WHERE user_participant_id = %s LIMIT 1", tg_id)
            conn.commit()


# Возвращает словарь с информацией о сессии хоста
async def get_quiz_session_info(code: int | str) -> dict:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Quiz_host_session WHERE code = %s LIMIT 1", str(code))
            return cursor.fetchone()


# Возвращает список словарей с информацией о сессии участника
async def get_quiz_participant_session_info(code: int | str) -> list[dict]:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Quiz_participant_session WHERE code = %s", str(code))
            return cursor.fetchall()


# Возвращает словарь с информацией о записи пользователя
async def get_user_record_info_by_id(id_: int) -> dict:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM User WHERE record_id = %s LIMIT 1", id_)
            return cursor.fetchone()


# Добавление статистики
async def add_statistics(
        type_: RecordTypes,
        participant_tg_id: int,
        host_tg_id: int,
        record_id: int,
        nickname: str,
        record_name: str,
        score: float,
        max_score: int,
        start_time: str,
        session_id: int = 0,
):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            tpl = (
                participant_tg_id,
                host_tg_id,
                record_id,
                nickname,
                record_name,
                score,
                max_score,
                start_time,
            )
            if type_ == RecordTypes.Test:
                cursor.execute(
                    "INSERT INTO test_statistics(tg_id, host_tg_id, record_id, nickname, record_name, score, max_score,"
                    "start_time) "
                    " VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
                    tpl
                )
            else:
                tpl = tpl + (session_id, )
                cursor.execute(
                    "INSERT INTO quiz_statistics(tg_id, host_tg_id, record_id, nickname, record_name, score, max_score,"
                    "start_time, session_id)"
                    " VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    tpl
                )
            conn.commit()


async def get_statistics_info_by_id(tg_host_id: int, type_: RecordTypes) -> list[dict]:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {'quiz_statistics' if type_ == RecordTypes.Quiz else 'test_statistics'} "
                f"WHERE host_tg_id = %s",
                tg_host_id
            )
            return cursor.fetchall()


async def get_record_name_by_id(record_id: int) -> str:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM user WHERE record_id = %s",
                record_id
            )
            return cursor.fetchone()['name']


async def set_new_deadline(record_id: int, deadline: str):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE User SET deadline = %s WHERE record_id = %s",
                (deadline, record_id)
            )
            conn.commit()


async def set_new_time_limit(record_id: int, seconds: int):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE User SET time_limit = %s WHERE record_id = %s",
                (seconds, record_id)
            )
            conn.commit()


async def delete_statistics_by_session_id(type_: RecordTypes, session_id: int = None, test_stat_id: int = None):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            if type_ == RecordTypes.Quiz:
                cursor.execute("DELETE FROM quiz_statistics WHERE session_id = %s", session_id)
            else:
                cursor.execute("DELETE FROM test_statistics WHERE id = %s", test_stat_id)
            conn.commit()


async def get_nickname_by_id(type_: RecordTypes, id_: int):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            if type_ == RecordTypes.Quiz:
                cursor.execute("SELECT nickname FROM quiz_statistics WHERE id = %s", id_)
            else:
                cursor.execute("SELECT nickname FROM test_statistics WHERE id = %s", id_)
            return cursor.fetchone()['nickname']


# Получить последний id, вставленное в таблицу <table>
async def get_last_inserted_id(table: str, cursor) -> int:
    cursor.execute(f"SELECT LAST_INSERT_ID() FROM {table}")
    return cursor.fetchone()['LAST_INSERT_ID()']
