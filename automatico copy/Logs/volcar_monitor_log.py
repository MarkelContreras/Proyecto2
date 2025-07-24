#!/usr/bin/env python3
import sys
import os
import re
from datetime import datetime, timedelta

# Agregar ruta de utils al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))
from config_db import get_connection

# Validación de argumentos
if len(sys.argv) < 4:
    print("Uso: {} <archivo_log> <programa> <session_id>".format(sys.argv[0]))
    exit(1)

LOG_FILE = sys.argv[1]
programa = sys.argv[2]

# Validar que session_id sea entero
try:
    session_id = int(sys.argv[3])
except ValueError:
    print("El ID de sesión debe ser un número entero.")
    exit(1)

# Preparar conexión a BD
conn = get_connection()
if conn is None:
    exit(1)

cursor = conn.cursor()

# Crear tabla si no existe
create_table = """
CREATE TABLE IF NOT EXISTS rendimiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    programa VARCHAR(100) NOT NULL,
    segundos INT NOT NULL,
    cpu FLOAT,
    memoria FLOAT,
    disco FLOAT,
    temperatura FLOAT,
    red_recibido FLOAT,
    red_enviado FLOAT
)
"""
cursor.execute(create_table)

# Procesar archivo
registros = []
start_time = None
segundos = 0

with open(LOG_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        if line.startswith("---"):
            fecha_hora_str = line.strip("- ").strip()
            dt = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M:%S")
            if start_time is None:
                start_time = dt
                segundos = 0
            else:
                segundos = int((dt - start_time).total_seconds())

        elif line.startswith("CPU:"):
            cpu = float(re.search(r"([\d.]+)", line).group(1))

        elif line.startswith("Memoria:"):
            memoria = float(re.search(r"([\d.]+)", line).group(1))

        elif line.startswith("Disco:"):
            disco = float(re.search(r"([\d.]+)", line).group(1))

        elif line.startswith("Temperatura"):
            temperatura = float(re.search(r"([\d.]+)", line).group(1))

        elif line.startswith("Red:"):
            match = re.search(r"Recibidos=([\d.,]+) (MB|GB), Enviados=([\d.,]+) (MB|GB)", line)
            if match:
                recibido_val = float(match.group(1).replace(',', '.'))
                recibido_unit = match.group(2)
                enviado_val = float(match.group(3).replace(',', '.'))
                enviado_unit = match.group(4)

                red_recibido = recibido_val * 1024 if recibido_unit == "GB" else recibido_val
                red_enviado = enviado_val * 1024 if enviado_unit == "GB" else enviado_val
            else:
                red_recibido = 0.0
                red_enviado = 0.0
                print(f"[!] No se pudo parsear red en línea: {line}")

            registros.append((
                session_id,
                programa,
                segundos,
                cpu,
                memoria,
                disco,
                temperatura,
                red_recibido,
                red_enviado
            ))

# Insertar en la base de datos
insert_query = """
INSERT INTO rendimiento 
(session_id, programa, segundos, cpu, memoria, disco, temperatura, red_recibido, red_enviado)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

insertados = 0
for r in registros:
    try:
        cursor.execute(insert_query, r)
        insertados += 1
    except Exception as e:
        print(f"[X] Error insertando registro: {e}")

conn.commit()
cursor.close()
conn.close()

print(f"✅ {insertados} registros insertados correctamente en la tabla 'rendimiento'.")
