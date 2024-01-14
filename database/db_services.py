import pymysql as mysql
from .config import mysql_db_name, mysql_db_username, mysql_db_password, mysql_host, mysql_port
from classes.question import Question
from enum import Enum
from cryptography.fernet import Fernet


key = Fernet.generate_key()
fernet = Fernet(key)


class Types(Enum):
    Quiz = 'Q'
    Test = 'T'


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


async def initialize_db():
    conn = db_connection()
    with conn:
        with conn.cursor() as cursor:
            create_db_query = "CREATE DATABASE IF NOT EXISTS {db_name}".format(db_name=mysql_db_name)
            use_db_query = "USE {db_name}".format(db_name=mysql_db_name)
            cursor.execute(create_db_query)
            cursor.execute(use_db_query)
            create_q_and_t_table_query = "CREATE TABLE IF NOT EXISTS Quiz_and_test(" \
                                         "id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT," \
                                         "name VARCHAR(100)," \
                                         "type ENUM('Q', 'T')" \
                                         ")"
            create_users_table_query = "CREATE TABLE IF NOT EXISTS User(" \
                                       "tg_id BIGINT UNSIGNED NOT NULL," \
                                       "quiz_or_test_id INT UNSIGNED," \
                                       "FOREIGN KEY (quiz_or_test_id) REFERENCES Quiz_and_test(id)" \
                                       ")"
            create_questions_table_query = "CREATE TABLE IF NOT EXISTS Question(" \
                                           "id INT UNSIGNED," \
                                           "FOREIGN KEY (id) REFERENCES Quiz_and_test(id)," \
                                           "question_text VARCHAR(200)," \
                                           "variants_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT" \
                                           ")"
            create_variants_table_query = "CREATE TABLE IF NOT EXISTS Variant(" \
                                          "id INT UNSIGNED," \
                                          "FOREIGN KEY (id) REFERENCES Question(variants_id)," \
                                          "variant_text VARCHAR(100)" \
                                          ")"
            create_right_variants_table_query = "CREATE TABLE IF NOT EXISTS Right_variant(" \
                                                "question_id INT UNSIGNED," \
                                                "FOREIGN KEY (question_id) REFERENCES Question(variants_id)," \
                                                "encrypted_text VARCHAR(228)" \
                                                ")"
            cursor.execute(create_q_and_t_table_query)
            cursor.execute(create_users_table_query)
            cursor.execute(create_questions_table_query)
            cursor.execute(create_variants_table_query)
            cursor.execute(create_right_variants_table_query)


async def insert_questions(user_tg_id: int, name: str, questions: list[Question], type_: Types):
    conn = db_connection(mysql_db_name)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO Quiz_and_test(name, type) VALUES(%s, %s)", (name, type_.value))
            conn.commit()

            cursor.execute("SELECT LAST_INSERT_ID() FROM Quiz_and_test")
            last_q_and_t_id = cursor.fetchone()['LAST_INSERT_ID()']
            cursor.execute("INSERT INTO User(tg_id, quiz_or_test_id) VALUES(%s, %s)", (user_tg_id, last_q_and_t_id))
            conn.commit()

            for question in questions:
                cursor.execute("INSERT INTO Question(id, question_text) VALUES(%s, %s)",
                               (last_q_and_t_id, question.question))
                conn.commit()
                cursor.execute("SELECT LAST_INSERT_ID() FROM Question")
                last_variant_id = cursor.fetchone()['LAST_INSERT_ID()']
                for variant in question.variants:
                    cursor.execute("INSERT INTO Variant(id, variant_text) VALUES(%s, %s)", (last_variant_id, variant))

                for right_variant in question.right_variants:
                    encrypted_variant = fernet.encrypt(right_variant.encode())
                    cursor.execute("INSERT INTO Right_variant(question_id, encrypted_text) VALUES(%s, %s)",
                                   (last_variant_id, encrypted_variant))
                conn.commit()
