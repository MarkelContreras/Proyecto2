import os

def seleccionar_archivo():
    ruta_actual = os.getcwd()

    while True:
        print(f"\n📂 Directorio actual: {ruta_actual}")
        elementos = os.listdir(ruta_actual)
        elementos.sort()

        # Separar carpetas y archivos
        carpetas = [e for e in elementos if os.path.isdir(os.path.join(ruta_actual, e))]
        archivos = [e for e in elementos if os.path.isfile(os.path.join(ruta_actual, e))]

        # Mostrar menú numerado
        print("0. .. (subir un nivel)")
        for idx, carpeta in enumerate(carpetas, start=1):
            print(f"{idx}. [📁] {carpeta}")
        for idx, archivo in enumerate(archivos, start=1 + len(carpetas)):
            print(f"{idx}. [📄] {archivo}")

        opcion = input("Selecciona un número (archivo para seleccionar, carpeta para entrar): ").strip()

        if not opcion.isdigit():
            print("❌ Entrada no válida. Introduce un número.")
            continue

        opcion = int(opcion)

        if opcion == 0:
            nueva_ruta = os.path.dirname(ruta_actual)
        elif 1 <= opcion <= len(carpetas):
            nueva_ruta = os.path.join(ruta_actual, carpetas[opcion - 1])
        elif len(carpetas) < opcion <= len(carpetas) + len(archivos):
            archivo_seleccionado = os.path.join(ruta_actual, archivos[opcion - 1 - len(carpetas)])
            print(f"\n✅ Archivo seleccionado: {archivo_seleccionado}")
            return archivo_seleccionado
        else:
            print("❌ Opción fuera de rango.")
            continue

        # Cambiar al nuevo directorio
        ruta_actual = nueva_ruta

# Ejemplo de uso directo
if __name__ == "__main__":
    archivo = seleccionar_archivo()
    print("\n🧾 Has seleccionado:", archivo)
