import os
import pyarrow.parquet as pq
import pandas as pd

BASE_DIR = "Parquet"

def listar_columnas_parquet():
    if not os.path.isdir(BASE_DIR):
        print(f"❌ La carpeta '{BASE_DIR}' no existe.")
        return

    for programa in sorted(os.listdir(BASE_DIR)):
        ruta_programa = os.path.join(BASE_DIR, programa)
        if not os.path.isdir(ruta_programa):
            continue

        print(f"\n📁 Programa: {programa}")

        for archivo in os.listdir(ruta_programa):
            if archivo.endswith(".parquet"):
                ruta_parquet = os.path.join(ruta_programa, archivo)
                try:
                    parquet_file = pq.ParquetFile(ruta_parquet)
                    columnas = parquet_file.schema.names
                    filas = parquet_file.metadata.num_rows
                    print(f"  🔹 {archivo}:")
                    print(f"     - Filas: {filas}")
                    print(f"     - Columnas: {columnas}")
                except Exception as e:
                    print(f"  ❌ Error al leer '{archivo}': {e}")

    # Vista previa corregida
    ruta_ligero = os.path.join(BASE_DIR, "fallara3", "resumen_fuzzing_ligero.parquet")
    if os.path.exists(ruta_ligero):
        print(f"\n🔍 Vista previa de 'resumen_fuzzing_ligero.parquet' de 'fallara3':")
        try:
            columnas = ["id", "session_id", "fecha_inicio", "hora_inicio", "fecha_fin", "hora_fin"]
            df = pd.read_parquet(ruta_ligero, columns=columnas)

            df_preview = df.head(10).copy()

            # Convertir hora a formato HH:MM:SS si es timedelta
            df_preview["hora_inicio"] = df_preview["hora_inicio"].apply(lambda x: str(x).split()[-1] if pd.notnull(x) else "")
            df_preview["hora_fin"] = df_preview["hora_fin"].apply(lambda x: str(x).split()[-1] if pd.notnull(x) else "")

            df_preview["inicio"] = pd.to_datetime(df_preview["fecha_inicio"].astype(str) + " " + df_preview["hora_inicio"])
            df_preview["fin"] = pd.to_datetime(df_preview["fecha_fin"].astype(str) + " " + df_preview["hora_fin"])
            df_preview["duracion_min"] = (df_preview["fin"] - df_preview["inicio"]).dt.total_seconds() / 60

            print(df_preview[["id", "session_id", "inicio", "fin", "duracion_min"]])
        except Exception as e:
            print(f"❌ Error al procesar vista previa: {e}")

if __name__ == "__main__":
    listar_columnas_parquet()
