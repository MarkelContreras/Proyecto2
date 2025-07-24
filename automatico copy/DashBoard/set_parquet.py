# DashBoard/set_parquet.py

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.config_db import get_connection

PARQUET_DIR = "Parquet"
os.makedirs(PARQUET_DIR, exist_ok=True)

def exportar_parquet(sql_query, nombre_archivo, chunksize=50000):
    conn = get_connection()
    if conn is None:
        print(f"❌ No se pudo conectar a la base de datos para leer '{nombre_archivo}'")
        return

    ruta_archivo = os.path.join(PARQUET_DIR, nombre_archivo)

    if os.path.exists(ruta_archivo):
        os.remove(ruta_archivo)

    writer = None
    for i, chunk in enumerate(pd.read_sql(sql_query, conn, chunksize=chunksize)):
        table = pa.Table.from_pandas(chunk)
        if writer is None:
            writer = pq.ParquetWriter(ruta_archivo, table.schema)
        writer.write_table(table)
        print(f"✅ Chunk {i + 1} guardado en {ruta_archivo} ({len(chunk)} filas)")

    if writer:
        writer.close()

    conn.close()
    print(f"✔️ {ruta_archivo} generado.\n")

def main():
    exportar_parquet(
        sql_query="""
            SELECT id, session_id, programa, exit_code,
                   fecha_inicio, hora_inicio, fecha_fin, hora_fin
            FROM fuzzing
        """,
        nombre_archivo="resumen_fuzzing_ligero.parquet"
    )

    exportar_parquet(
        sql_query="""
            SELECT id, session_id, programa, input
            FROM fuzzing
        """,
        nombre_archivo="fuzzing_inputs.parquet"
    )

    exportar_parquet(
        sql_query="SELECT * FROM rendimiento",
        nombre_archivo="resumen_rendimiento.parquet"
    )

if __name__ == "__main__":
    main()
