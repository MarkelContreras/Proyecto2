

import pandas as pd
import os
import time

def verificar_archivo(path):
    if not os.path.exists(path):
        print(f"❌ Archivo no encontrado: {path}")
        return None, None
    try:
        start = time.time()
        df = pd.read_parquet(path)
        end = time.time()
        duracion = end - start

        print(f"📁 {path} cargado correctamente:")
        print(f"   - Filas: {len(df)}")
        print(f"   - Columnas: {df.columns.tolist()}")
        print(f"   ⏱️ Tiempo de carga: {duracion:.2f} segundos\n")

        return df, duracion
    except Exception as e:
        print(f"❌ Error al cargar {path}: {e}")
        return None, None

def guardar_por_programa(df_ligero, df_inputs, df_rend, carpeta_base="Parquet"):
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

def main():
    df_ligero, t1 = verificar_archivo("resumen_fuzzing_ligero.parquet")
    df_inputs, t2 = verificar_archivo("fuzzing_inputs.parquet")
    df_rend,   t3 = verificar_archivo("resumen_rendimiento.parquet")

    if df_ligero is None or df_inputs is None or df_rend is None:
        print("🚫 No se pueden procesar por errores de carga.")
        return

    if not all("programa" in df.columns for df in [df_ligero, df_inputs, df_rend]):
        print("🚫 Todos los archivos deben contener la columna 'programa'.")
        return

    guardar_por_programa(df_ligero, df_inputs, df_rend)

    print("\n🕒 Tiempos de carga:")
    if t1 is not None: print(f" - resumen_fuzzing_ligero: {t1:.2f} s")
    if t2 is not None: print(f" - fuzzing_inputs:         {t2:.2f} s")
    if t3 is not None: print(f" - resumen_rendimiento:    {t3:.2f} s")

if __name__ == "__main__":
    main()
