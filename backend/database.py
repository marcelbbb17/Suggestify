import mysql.connector
from config import get_config

def get_db_connection():
    config = get_config()
    connection = mysql.connector.connect(
        host = config.DB_HOST,
        port = config.DB_PORT,
        user = config.DB_USER,
        password = config.DB_PASSWORD,
        database = config.DB_NAME
    )
    return connection