import mysql.connector

def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="markeladmin",
            database="autoprueba"
        )
    except mysql.connector.Error as err:
        print("❌ Error al conectar con la base de datos:", err)
        return None
