import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.config_db import get_connection

PARQUET_DIR = os.path.join(os.path.dirname(__file__), "Parquet")
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


def verificar_archivo(path):
    if not os.path.exists(path):
        print(f"❌ Archivo no encontrado: {path}")
        return None, None
    try:
        start = time.time()
        df = pd.read_parquet(path)
        duracion = time.time() - start
        print(f"📁 {path} cargado correctamente:")
        print(f"   - Filas: {len(df)}")
        print(f"   - Columnas: {df.columns.tolist()}")
        print(f"   ⏱️ Tiempo de carga: {duracion:.2f} segundos\n")
        return df, duracion
    except Exception as e:
        print(f"❌ Error al cargar {path}: {e}")
        return None, None


def guardar_por_programa(df_ligero, df_inputs, df_rend, carpeta_base=PARQUET_DIR):
    programas = sorted(set(df_ligero["programa"].unique()) |
                       set(df_inputs["programa"].unique()) |
                       set(df_rend["programa"].unique()))

    for programa in programas:
        nombre_limpio = str(programa).replace(" ", "_").replace("/", "_")
        ruta_prog = os.path.join(carpeta_base, nombre_limpio)
        os.makedirs(ruta_prog, exist_ok=True)

        sub_ligero = df_ligero[df_ligero["programa"] == programa]
        sub_inputs = df_inputs[df_inputs["programa"] == programa]
        sub_rend   = df_rend[df_rend["programa"] == programa]

        print(f"\n🔧 Guardando datos para: {programa}")
        print(f"   - Ligero: {len(sub_ligero)} filas")
        print(f"   - Inputs: {len(sub_inputs)} filas")
        print(f"   - Rendimiento: {len(sub_rend)} filas")

        sub_ligero.to_parquet(os.path.join(ruta_prog, "resumen_fuzzing_ligero.parquet"), index=False)
        sub_inputs.to_parquet(os.path.join(ruta_prog, "fuzzing_inputs.parquet"), index=False)
        sub_rend.to_parquet(os.path.join(ruta_prog, "resumen_rendimiento.parquet"), index=False)

        print(f"   ✅ Archivos guardados en: {ruta_prog}")


def borrar_generales():
    print("\n🧹 Eliminando archivos generales...")
    archivos = [
        "resumen_fuzzing_ligero.parquet",
        "fuzzing_inputs.parquet",
        "resumen_rendimiento.parquet"
    ]
    for nombre in archivos:
        ruta = os.path.join(PARQUET_DIR, nombre)
        if os.path.exists(ruta):
            os.remove(ruta)
            print(f"🗑️ {nombre} eliminado.")
        else:
            print(f"⚠️ {nombre} no encontrado para borrar.")


def main():
    # Paso 1: Exportar los archivos generales
    exportar_parquet(
        sql_query="""
            SELECT id, session_id, programa, exit_code,
                   fecha_inicio, hora_inicio, fecha_fin, hora_fin
            FROM fuzzing
        """,
        nombre_archivo="resumen_fuzzing_ligero.parquet"
    )

    exportar_parquet(
        sql_query="""SELECT id, session_id, programa, input FROM fuzzing""",
        nombre_archivo="fuzzing_inputs.parquet"
    )

    exportar_parquet(
        sql_query="SELECT * FROM rendimiento",
        nombre_archivo="resumen_rendimiento.parquet"
    )

    # Paso 2: Verificar archivos
    df_ligero, t1 = verificar_archivo(os.path.join(PARQUET_DIR, "resumen_fuzzing_ligero.parquet"))
    df_inputs, t2 = verificar_archivo(os.path.join(PARQUET_DIR, "fuzzing_inputs.parquet"))
    df_rend,   t3 = verificar_archivo(os.path.join(PARQUET_DIR, "resumen_rendimiento.parquet"))

    if any(df is None for df in (df_ligero, df_inputs, df_rend)):
        print("🚫 No se pueden procesar por errores de carga.")
        return

    if not all("programa" in df.columns for df in [df_ligero, df_inputs, df_rend]):
        print("🚫 Todos los archivos deben contener la columna 'programa'.")
        return

    # Paso 3: Guardar por programa
    guardar_por_programa(df_ligero, df_inputs, df_rend)

    # Paso 4: Eliminar los archivos generales
    borrar_generales()

    print("\n🕒 Tiempos de carga:")
    if t1 is not None: print(f" - resumen_fuzzing_ligero: {t1:.2f} s")
    if t2 is not None: print(f" - fuzzing_inputs:         {t2:.2f} s")
    if t3 is not None: print(f" - resumen_rendimiento:    {t3:.2f} s")


if __name__ == "__main__":
    main()
