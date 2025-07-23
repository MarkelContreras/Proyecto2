from utils.config_db import get_connection, get_database_name
import mysql.connector

def create_database_and_tables():
    db_name = get_database_name()
    try:
        conn = get_connection(include_db=False)
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Base de datos '{db_name}' creada.")
        else:
            print(f"ℹ️ La base de datos '{db_name}' ya existe.")

        cursor.execute(f"USE {db_name}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispositivos (
                id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                ip VARCHAR(50) NOT NULL,
                usuario VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                arquitectura VARCHAR(50)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fuzzing (
                id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                session_id INT(11) NOT NULL,
                programa VARCHAR(100) NOT NULL,
                input TEXT NOT NULL,
                exit_code INT(11) NOT NULL,
                fecha_inicio DATE,
                hora_inicio TIME,
                fecha_fin DATE,
                hora_fin TIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rendimiento (
                id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                session_id INT(11) NOT NULL,
                programa VARCHAR(100) NOT NULL,
                segundos INT(11) NOT NULL,
                cpu FLOAT,
                memoria FLOAT,
                disco FLOAT,
                temperatura FLOAT,
                red_recibido FLOAT,
                red_enviado FLOAT
            )
        """)

        print("✅ Tablas listas en la base de datos.")

    except mysql.connector.Error as err:
        print(f"❌ Error durante la creación de la base de datos: {err}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
