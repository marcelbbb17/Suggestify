import mysql.connector

def get_db_connection():
  connection = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = 'DonquixoteDoflamingo88',
    database = 'suggestify'
  )
  return connection