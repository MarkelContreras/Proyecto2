import mysql.connector
from sqlalchemy import create_engine


def get_database_name():
    #return "testDB"
    return "autoprueba"

def get_connection(database=None):
    """Establece y retorna una conexión a la base de datos."""
    db_name = database if database else get_database_name()
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="markeladmin",
        database=db_name
    )


def createDb():
    """Comprueba si la base de datos existe y la crea si no. Retorna True si se creó, False si ya existía."""
    db_name = get_database_name()
    
    # Conexión sin base de datos para poder crearla si no existe
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="markeladmin"
    )
    cursor = conn.cursor()

    cursor.execute("SHOW DATABASES")
    databases = [row[0] for row in cursor.fetchall()]

    if db_name not in databases:
        cursor.execute(f"CREATE DATABASE {db_name}")
        conn.commit()
        resultado = True
    else:
        resultado = False

    cursor.close()
    conn.close()
    return resultado



def create_table_dispositivos():
    conn = get_connection(get_database_name())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispositivos (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            ip VARCHAR(50) NOT NULL,
            usuario VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            arquitectura VARCHAR(50)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def create_table_fuzzing():
    conn = get_connection(get_database_name())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fuzzing (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            programa VARCHAR(100) NOT NULL,
            input TEXT NOT NULL,
            exit_code INT NOT NULL,
            fecha_inicio DATE,
            hora_inicio TIME,
            fecha_fin DATE,
            hora_fin TIME
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def create_tables_if_not_exist():
    create_table_dispositivos()
    create_table_fuzzing()

def get_engine():
    """Devuelve un motor SQLAlchemy para acceder a la base de datos."""
    user = "root"
    password = "markeladmin"
    host = "localhost"
    database = "testDB"  # <- cámbialo por el tuyo real
    port = 3306

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(url)
    return engine

# config_db.py
import connectorx as cx
import duckdb

def get_duckdb_connection():
    conn_str = "mysql://root:markeladmin@localhost/testDB"
    query = "SELECT * FROM fuzzing"

    try:
        df = cx.read_sql(conn_str, query)
        duck_con = duckdb.connect()
        duck_con.register("fuzzing_data", df)
        return duck_con
    except Exception as e:
        print(f"Error loading data into DuckDB: {e}")
        return None
