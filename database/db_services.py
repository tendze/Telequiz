import pymysql as mysql
from .config import mysql_db_name, mysql_db_username, mysql_db_password, mysql_host, mysql_port
from classes.question import Question
from enum import Enum
from cryptography.fernet import Fernet


key = Fernet.generate_key()
fernet = Fernet(key)


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
                                       "type ENUM('Q', 'T')" \
                                       ")"
            create_questions_table_query = "CREATE TABLE IF NOT EXISTS Question(" \
                                           "id INT UNSIGNED," \
                                           "FOREIGN KEY (id) REFERENCES User(record_id)," \
                                           "question_text VARCHAR(200)," \
                                           "variants_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT" \
                                           ")"
            create_variants_table_query = "CREATE TABLE IF NOT EXISTS Variant(" \
                                          "id INT UNSIGNED," \
                                          "FOREIGN KEY (id) REFERENCES Question(variants_id)," \
                                          "variant_text VARCHAR(100)" \
                                          ")"
            create_right_variants_table_query = "CREATE TABLE IF NOT EXISTS Right_variant(" \
                                                "id INT UNSIGNED," \
                                                "FOREIGN KEY (id) REFERENCES Question(variants_id)," \
                                                "encrypted_text VARCHAR(228)" \
                                                ")"
            cursor.execute(create_users_table_query)
            cursor.execute(create_questions_table_query)
            cursor.execute(create_variants_table_query)
            cursor.execute(create_right_variants_table_query)


# Вставляет данные после в таблицы User, Question, Variant и Right_variant
async def insert_questions(user_tg_id: int, name: str, questions: list[Question], type_: Types):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO User(tg_id, name, type) VALUES(%s, %s, %s)", (user_tg_id, name, type_.value))
            conn.commit()

            cursor.execute("SELECT LAST_INSERT_ID() FROM User")
            last_user_record_id = cursor.fetchone()['LAST_INSERT_ID()']

            for question in questions:
                cursor.execute("INSERT INTO Question(id, question_text) VALUES(%s, %s)",
                               (last_user_record_id, question.question))
                conn.commit()
                cursor.execute("SELECT LAST_INSERT_ID() FROM Question")
                last_variant_id = cursor.fetchone()['LAST_INSERT_ID()']
                for variant in question.variants:
                    cursor.execute("INSERT INTO Variant(id, variant_text) VALUES(%s, %s)", (last_variant_id, variant))

                for right_variant in question.right_variants:
                    encrypted_variant = fernet.encrypt(right_variant.encode())
                    cursor.execute("INSERT INTO Right_variant(id, encrypted_text) VALUES(%s, %s)",
                                   (last_variant_id, encrypted_variant))
                conn.commit()


# Возващает словарь вида record_id: name, где record_id - айди записи, а name - название квиза/теста
async def get_user_type_names(tg_id: int, type_: Types) -> dict[int, str]:
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT record_id, name FROM User WHERE tg_id = %s AND type = %s", (tg_id, type_.value))
            user_q_or_t_id = cursor.fetchall()
            return user_q_or_t_id
