import mysql.connector


_DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "markeladmin",
    "database": "autoprueba"
}

def get_database_name():
    return _DB_CONFIG["database"]

def get_connection(include_db=True):
    """Devuelve una conexión a la base de datos.
       Si include_db=False, no se incluye el nombre de la base de datos (para crearla si no existe).
    """
    config = _DB_CONFIG.copy()
    if not include_db:
        config.pop("database")

    try:
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        print("❌ Error al conectar con la base de datos:", err)
        return None
