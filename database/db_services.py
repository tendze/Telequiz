import pymysql as mysql
from .config import mysql_db_name, mysql_db_username, mysql_db_password, mysql_host, mysql_port
from classes.question import Question
from enum import Enum
from encrypting.question_encripting import encrypt_text, decrypt_bytes


# Класс, представляющий квиз/тест
class Types(Enum):
    Quiz = 'Q'
    Test = 'T'


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
                                       "time_limit INT UNSIGNED" \
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
            create_quiz_codes_table_query = "CREATE TABLE IF NOT EXISTS Quiz_codes(" \
                                            "id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT NOT NULL," \
                                            "code INT NOT NULL," \
                                            "user_host_id BIGINT UNSIGNED NOT NULL," \
                                            "start_time DATETIME" \
                                            ")"
            cursor.execute(create_users_table_query)
            cursor.execute(create_questions_table_query)
            cursor.execute(create_variants_table_query)
            cursor.execute(create_right_variants_table_query)


# Вставляет данные после в таблицы User, Question, Variant и Right_variant
async def insert_questions(user_tg_id: int,
                           name: str,
                           questions: list[Question],
                           type_: Types,
                           quiz_timer: int):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO User(tg_id, name, type, time_limit) VALUES(%s, %s, %s, %s)",
                           (user_tg_id, name, type_.value, None if quiz_timer == 0 else quiz_timer))
            conn.commit()

            cursor.execute("SELECT LAST_INSERT_ID() FROM User")
            last_user_record_id = cursor.fetchone()['LAST_INSERT_ID()']

            for question in questions:
                cursor.execute("INSERT INTO Question(id, question_text, consider_partial_answers) VALUES(%s, %s, %s)",
                               (last_user_record_id, question.question, 1 if question.consider_partial_answers == 1 else 0))
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
async def get_user_record_names(tg_id: int, type_: Types) -> dict[int, str]:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT record_id, name FROM User WHERE tg_id = %s AND type = %s", (tg_id, type_.value))
            user_q_or_t_id = cursor.fetchall()
            return user_q_or_t_id


async def get_user_record_questions(record_id: int) -> list[Question]:
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
                questions.append(Question(question=data['question_text'],
                                          variants=data['variants'],
                                          right_variants=data['right_variants'],
                                          consider_partial_answers=True if int.from_bytes(data['consider_partial_answers'],
                                                                                          byteorder='little') == 1
                                          else False))
            return questions


async def delete_user_record(record_id: int):
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
