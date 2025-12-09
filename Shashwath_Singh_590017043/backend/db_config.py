import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1954",  # ✔️ Your MySQL password
        database="ecommerce_db"
    )
