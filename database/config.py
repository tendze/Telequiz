from environs import Env
import os

env = Env()
env.read_env()

mysql_host = os.getenv('HOST')
mysql_port = os.getenv('PORT')
mysql_db_username = os.getenv('DB_USERNAME')
mysql_db_password = os.getenv('DB_PASSWORD')
mysql_db_name = os.getenv('DB_NAME')
