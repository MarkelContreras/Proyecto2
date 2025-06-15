import subprocess
import time
import os
import shutil
import socket
import sys

class DuplicadorSalida:
    def __init__(self, archivo):
        self.consola = sys.__stdout__
        self.archivo = open(archivo, "w", buffering=1)  # Línea por línea

    def write(self, mensaje):
        self.consola.write(mensaje)
        self.archivo.write(mensaje)

    def flush(self):
        self.consola.flush()
        self.archivo.flush()

# Duplicamos stdout y stderr a consola + archivo
sys.stdout = DuplicadorSalida("ejecucion.txt")
sys.stderr = sys.stdout



# --- Configuración fija ---
REMOTE_USER = "markel"
REMOTE_IP = "172.16.124.103"
REMOTE_DIR = "/home/markel/Documents/automatico"
LOGS_DIR = "Logs"
PROCESAR_SCRIPT = os.path.join(LOGS_DIR, "procesarLogs.py")
programa = "rendimiento1"

# --- Función para esperar a que el servidor esté completamente operativo ---
def esperar_socket_abierto(ip, puerto, timeout=30):
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            with socket.create_connection((ip, puerto), timeout=2) as sock:
                sock.sendall(b'PING\n')  # Confirmamos que acepta datos
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(1)
    return False

# --- Entrada del usuario ---
num_iteraciones = int(input("Número de sesiones a ejecutar: "))
sesion_inicial = int(input("Número de sesión inicial (ej. 0): "))
duracion_sesion = int(input("¿Cuánto tiempo debe durar cada sesión? (en segundos): "))

# --- Comienza el bucle de sesiones ---
for i in range(num_iteraciones):
    sesion_actual = sesion_inicial + i
    print(f"\n🔁 [Iteración {i+1}/{num_iteraciones}] - Sesión #{sesion_actual}\n")

    # 1. Limpiar procesos python3 en remoto
    print("🧹 Matando procesos 'python3' en la Raspberry Pi antes de lanzar el servidor...")
    try:
        kill_python_cmd = (
            f"ssh {REMOTE_USER}@{REMOTE_IP} "
            "\"ps aux | grep python3 | grep -v grep | awk '{print \\$2}' | xargs -r kill -9\""
        )
        subprocess.run(kill_python_cmd, shell=True)
        print("✅ Procesos python3 eliminados.")
    except Exception as e:
        print(f"⚠️  Error al intentar limpiar procesos python3: {e}")

    # 2. Lanzar servidor remoto
    print("🚀 Lanzando servidor remoto...")
    try:
        remote_command = f"cd {REMOTE_DIR} && python3 servidor.py {programa}"
        server_proc = subprocess.Popen([
            "ssh", f"{REMOTE_USER}@{REMOTE_IP}", remote_command
        ])
        time.sleep(2)
    except Exception as e:
        print(f"❌ Error al lanzar el servidor remoto: {e}")
        print("⏳ Esperando 1 minuto por si se recupera la conexión de red...")
        time.sleep(60)
        continue

    # 2.1 Esperar a que el puerto esté listo
    print("⏳ Esperando a que el servidor escuche en el puerto 1234...")
    if not esperar_socket_abierto(REMOTE_IP, 1234, timeout=30):
        print("❌ El servidor no respondió en el puerto 1234.")
        print("⏳ Esperando 1 minuto por si se recupera la conexión de red...")
        time.sleep(60)
        continue
    print("✅ Servidor disponible en el puerto 1234.")


    # 3. Matar posibles procesos de AFL previos
    print("🧹 Matando procesos anteriores de afl-fuzz...")
    subprocess.run("ps aux | grep afl-fuzz | awk '{print $2}' | xargs kill -9", shell=True)

    # 4. Lanzar AFL++
    print(f"🧨 Lanzando fuzzer local (duración: {duracion_sesion} segundos)...")
    try:
        fuzzer_command = (
            f"cd Fuzzing && "
            f"afl-fuzz -n -i inputs -o outputs -t 5000 -m none -- "
            f"./wrapper_fuzzing.sh @@"
        )

        fuzzer_process = subprocess.Popen(fuzzer_command, shell=True)
    except Exception as e:
        print(f"❌ Error al lanzar el fuzzer: {e}")
        continue

    print(f"⏳ Esperando {duracion_sesion} segundos de ejecución...")
    time.sleep(duracion_sesion)

    print("🛑 Matando proceso afl-fuzz...")
    subprocess.run("ps aux | grep afl-fuzz | awk '{print $2}' | xargs kill -9", shell=True)

    # 5. Matar servidor remoto
    print("🛑 Deteniendo servidor remoto...")
    try:
        kill_server_cmd = (
            f"ssh {REMOTE_USER}@{REMOTE_IP} "
            "\"ps aux | grep servidor.py | grep -v grep | awk '{print \\$2}' | xargs -r kill -9\""
        )
        subprocess.run(kill_server_cmd, shell=True)
        print("✅ Servidor remoto detenido correctamente.")
    except Exception as e:
        print(f"⚠️  Error al intentar detener el servidor remoto: {e}")

    # 6. Copiar log remoto
    remote_log_path = f"{REMOTE_USER}@{REMOTE_IP}:{REMOTE_DIR}/Logs/{programa}_log.txt"
    local_log_path = os.path.join(LOGS_DIR, f"{programa}_log.txt")

    print(f"📥 Copiando log desde la Raspberry Pi: {remote_log_path}")
    result = subprocess.run(["scp", remote_log_path, local_log_path], capture_output=True)

    if result.returncode != 0:
        print(f"❌ Error al copiar el log:\n{result.stderr.decode()}")
        continue
    else:
        print("✅ Log copiado correctamente.")

    # 7. Verificar existencia del log
    if not os.path.exists(local_log_path):
        print(f"❌ No se encontró el log esperado: {local_log_path}")
        continue

    # 8. Procesar log
    print("🧼 Procesando log y guardando en BD...")
    try:
        subprocess.run([
            "python3", PROCESAR_SCRIPT, local_log_path, programa, str(sesion_actual)
        ], check=True)
        print("✅ Log volcado correctamente en la base de datos.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al procesar log: {e}")
        nuevo_nombre = os.path.join(LOGS_DIR, f"error_sesion_{sesion_actual}.txt")
        try:
            shutil.move(local_log_path, nuevo_nombre)
            print(f"📁 Log renombrado a {nuevo_nombre}")
        except Exception as err:
            print(f"⚠️  No se pudo renombrar el log: {err}")

print("\n✅ Todas las iteraciones han terminado.")
