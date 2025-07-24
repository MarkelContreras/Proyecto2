import subprocess
import time
import os
import shutil
import socket
import sys
from utils.setup_db import create_database_and_tables
from dispositivos.dispositivos import lanzar_menu_dispositivos, dispositivo_actual
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "programa"))

from programa.programa import seleccionar_archivo
import shutil




# Clase para duplicar la salida de la consola en un archivo de log (ejecucion.txt)
class DuplicadorSalida:
    def __init__(self, archivo):
        self.consola = sys.__stdout__
        self.archivo = open(archivo, "w", buffering=1)  # Abre el archivo en modo escritura, con buffering lineal

    def write(self, mensaje):
        self.consola.write(mensaje)          # Escribe en la consola
        self.archivo.write(mensaje)           # Escribe en el archivo

    def flush(self):
        self.consola.flush()                 # Vacía el buffer de la consola
        self.archivo.flush()                 # Vacía el buffer del archivo

# Redirigir stdout y stderr para que la salida se duplique en ejecucion.txt
sys.stdout = DuplicadorSalida("ejecucion.txt")
sys.stderr = sys.stdout

create_database_and_tables()

# Menú de selección de dispositivo
lanzar_menu_dispositivos()

# Usar el dispositivo seleccionado
REMOTE_USER = dispositivo_actual["usuario"]
REMOTE_IP = dispositivo_actual["ip"]
REMOTE_DIR = f"/home/{REMOTE_USER}/Documents/automaticoTest"



# ---------------------- CONFIGURACIÓN ---------------------- #

# Parámetros de conexión y rutas remotas
REMOTE_USER = "markel"
REMOTE_IP = "172.16.124.103"
REMOTE_DIR = "/home/markel/Documents/automaticoTest"

# Directorio y scripts para el manejo de logs
LOGS_DIR = "Logs"
PROCESAR_SCRIPT = os.path.join(LOGS_DIR, "procesarLogs.py")
VOLCAR_SCRIPT = os.path.join(LOGS_DIR, "volcar_monitor_log.py")


# ---------------------- SELECCIÓN DE ARCHIVO C ---------------------- #

print("📌 Ahora vamos a seleccionar el archivo C que se usará...")
time.sleep(3)

# Seleccionar archivo fuente
while True:
    programa_path = seleccionar_archivo()

    if not programa_path.endswith(".c"):
        print("❌ El archivo seleccionado no es un archivo .c. Por favor, selecciona uno válido.")
    else:
        break

# Preguntar nuevo nombre (sin .c)
while True:
    nuevo_nombre = input("📝 Introduce el nuevo nombre del programa (sin extensión .c): ").strip()
    if not nuevo_nombre:
        print("⚠️ El nombre no puede estar vacío.")
    elif not nuevo_nombre.isidentifier():
        print("⚠️ Usa un nombre válido (letras, números, guiones bajos).")
    else:
        break

# Definir nuevo destino con nuevo nombre
destino = os.path.join("programa", f"{nuevo_nombre}.c")
programa = nuevo_nombre  # este es el nombre base que usarás en el resto del script

# Verificar si ya existe
if os.path.exists(destino):
    respuesta = input(f"⚠️ Ya existe '{destino}'. ¿Deseas sobrescribirlo? (s/n): ").strip().lower()
    if respuesta != "s":
        print("❌ Copia cancelada por el usuario.")
        sys.exit(0)

# Copiar archivo al nuevo destino
try:
    shutil.copy(programa_path, destino)
    print(f"📥 Archivo copiado correctamente a 'programa/{nuevo_nombre}.c'.")
except Exception as e:
    print(f"❌ Error al copiar el archivo: {e}")
    sys.exit(1)




# ---------------------- SETUP DE CARPETAS ---------------------- #

# Crear carpetas locales de logs si no existen
os.makedirs(os.path.join(LOGS_DIR, "rendimientoRasberry", programa), exist_ok=True)
os.makedirs(os.path.join(LOGS_DIR, "FuzzingRasberry", programa), exist_ok=True)

# Crear carpetas remotas necesarias
carpetas_remotas = [
    REMOTE_DIR,
    f"{REMOTE_DIR}/Logs/FuzzingRasberry/{programa}",
    f"{REMOTE_DIR}/Logs/MonitoreoRaspy/{programa}"
]

print("📁 Verificando/creando carpetas remotas en la Raspberry...")
for carpeta in carpetas_remotas:
    cmd = f"ssh {REMOTE_USER}@{REMOTE_IP} 'mkdir -p {carpeta}'"
    resultado = subprocess.run(cmd, shell=True)
    if resultado.returncode != 0:
        print(f"❌ Error al crear/verificar carpeta remota: {carpeta}")
        sys.exit(1)
print("✅ Carpetas remotas verificadas o creadas correctamente.")

# ------------------- COMPILACIÓN SEGÚN ARQUITECTURA DESDE BD ------------------- #

arquitectura = dispositivo_actual["arquitectura"]

if arquitectura == "arm":
    compilador = "arm-linux-gnueabihf-gcc"
    flags = "-static"
elif arquitectura == "x86":
    compilador = "gcc -m32"
    flags = ""
elif arquitectura == "x86_64":
    compilador = "gcc -m64"
    flags = ""
else:
    print(f"❌ Arquitectura no reconocida en la base de datos: {arquitectura}")
    sys.exit(1)

print(f"🔧 Compilando para arquitectura '{arquitectura}' con el compilador '{compilador}'...")

# ------------------- COMPILACIÓN CRUZADA ------------------- #

fuente_c = os.path.join("programa", f"{programa}.c")
binario_compilado = os.path.join("programa", programa)

if not os.path.isfile(fuente_c):
    print(f"❌ Archivo fuente no encontrado: {fuente_c}")
    sys.exit(1)

gcc_cmd = f"{compilador} {flags} -o {binario_compilado} {fuente_c}"
resultado = subprocess.run(gcc_cmd, shell=True)

if resultado.returncode != 0:
    print("❌ Error al compilar el binario.")
    sys.exit(1)

print(f"✅ Binario compilado correctamente: {binario_compilado}")


# ------------------- ENVÍO DE ARCHIVOS A LA RASPBERRY ------------------- #

if arquitectura == "arm":
    print("📤 Enviando binario al entorno automaticoTest en la Raspberry...")
    scp_destino = f"{REMOTE_USER}@{REMOTE_IP}:{REMOTE_DIR}/{programa}"
    resultado = subprocess.run(["scp", binario_compilado, scp_destino])
    if resultado.returncode != 0:
        print("❌ Error al copiar el binario a la Raspberry.")
        sys.exit(1)
    print("✅ Binario enviado correctamente.")

print("📤 Enviando servidor.py a la Raspberry...")
servidor_local = os.path.join("raspyArchivos", "servidor.py")
servidor_remoto = f"{REMOTE_USER}@{REMOTE_IP}:{REMOTE_DIR}/servidor.py"
resultado = subprocess.run(["scp", servidor_local, servidor_remoto])
if resultado.returncode != 0:
    print("❌ Error al copiar servidor.py a la Raspberry.")
    sys.exit(1)
print("✅ servidor.py enviado correctamente.")

print("📤 Enviando monitoreo.py a la Raspberry...")
monitoreo_local = os.path.join("raspyArchivos", "monitoreo.py")
monitoreo_remoto = f"{REMOTE_USER}@{REMOTE_IP}:{REMOTE_DIR}/monitoreo.py"
resultado = subprocess.run(["scp", monitoreo_local, monitoreo_remoto])
if resultado.returncode != 0:
    print("❌ Error al copiar monitoreo.py a la Raspberry.")
    sys.exit(1)
print("✅ monitoreo.py enviado correctamente.")


# ---------------------- FUNCIÓN: ESPERAR SOCKET ---------------------- #

def esperar_socket_abierto(ip, puerto, timeout=30):
    """
    Espera hasta que se pueda establecer una conexión TCP con el socket.
    Retorna True si la conexión es exitosa en el tiempo dado, False en caso contrario.
    """
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            with socket.create_connection((ip, puerto), timeout=2) as sock:
                sock.sendall(b'PING\n')
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(1)
    return False

# --------------------- CONFIGURACIÓN DE SESIONES --------------------- #

# Solicitar al usuario el número de sesiones, sesión inicial y duración de cada sesión
num_iteraciones = int(input("Número de sesiones a ejecutar: "))
sesion_inicial = int(input("Número de sesión inicial (ej. 0): "))
duracion_sesion = int(input("¿Cuánto tiempo debe durar cada sesión? (en segundos): "))

# --------------------- BUCLE DE EJECUCIÓN DE SESIONES --------------------- #

for i in range(num_iteraciones):
    sesion_actual = sesion_inicial + i
    sesion_str = f"sesion_{sesion_actual}"
    print(f"\n📘 [Iteración {i+1}/{num_iteraciones}] - Sesión #{sesion_actual}\n")

    # --- 1. Limpiar directorio de resultados del fuzzing --- #
    print("🧹 Borrando el contenido del directorio 'Fuzzing/outputs/'...")
    try:
        shutil.rmtree("Fuzzing/outputs")
        print("✅ outputs/ eliminado.")
    except Exception as e:
        print(f"⚠️  Error al eliminar outputs/: {e}")

    # --- 2. Lanzar monitoreo remoto en segundo plano --- #
    print("📱 [DEBUG] Lanzando monitoreo remoto en segundo plano...")
    try:
        start_monitor_cmd = (
            f"ssh -f {REMOTE_USER}@{REMOTE_IP} "
            f"'cd {REMOTE_DIR} && nohup python3 monitoreo.py {programa} {sesion_actual} {duracion_sesion} > /dev/null 2>&1 &'"
        )
        resultado = subprocess.run(start_monitor_cmd, shell=True)
        if resultado.returncode == 0:
            print("✅ Monitoreo iniciado.")
        else:
            print("❌ Error al lanzar el monitoreo.")
    except Exception as e:
        print(f"⚠️  Error al iniciar el monitoreo remoto: {e}")



    # --- 3. Terminar procesos antiguos de servidor (python3) en la Raspberry --- #
    print("🧹 [DEBUG] Matando procesos 'python3' antiguos en la Raspberry...")
    try:
        kill_python_cmd = (
            f"ssh {REMOTE_USER}@{REMOTE_IP} "
            "\"pwd && ps aux | grep servidor.py | grep -v grep | awk '{print \\$2}' | xargs -r kill -9\""
        )
        subprocess.run(kill_python_cmd, shell=True)
        print("✅ Procesos python3 eliminados.")
    except Exception as e:
        print(f"⚠️  Error al limpiar procesos python3: {e}")

    # --- 4. Lanzar el servidor remoto en segundo plano --- #
    print("🚀 [DEBUG] Lanzando servidor remoto en segundo plano...")
    try:
        remote_command = (
            f"ssh -f {REMOTE_USER}@{REMOTE_IP} "
            f"'cd {REMOTE_DIR} && pwd && nohup python3 servidor.py {programa} {sesion_actual} > /dev/null 2>&1 &'"
        )
        subprocess.run(remote_command, shell=True)
        print("✅ Servidor remoto iniciado.")
    except Exception as e:
        print(f"❌ Error al lanzar el servidor remoto: {e}")
        time.sleep(60)
        continue

    # --- 5. Esperar que el servidor remoto abra el puerto 1234 --- #
    print("⏳ Esperando a que el servidor escuche en el puerto 1234...")
    if not esperar_socket_abierto(REMOTE_IP, 1234, timeout=30):
        print("❌ El servidor no respondió en el puerto 1234.")
        time.sleep(60)
        continue
    print("✅ Servidor disponible.")

    # --- 6. Matar procesos anteriores de afl-fuzz en el sistema local --- #
    print("🧹 Matando procesos anteriores de afl-fuzz...")
    subprocess.run("ps aux | grep afl-fuzz | grep -v grep | awk '{print $2}' | xargs -r kill -9", shell=True)

    # --- 7. Lanzar el fuzzer local durante el tiempo especificado --- #
    print(f"💨 Lanzando fuzzer local durante {duracion_sesion} segundos...")
    try:
        fuzzer_command = (
            f"cd Fuzzing && afl-fuzz -n -i inputs -o outputs -t 5000 -m none -- /bin/bash ./wrapper_fuzzing.sh @@"
        )
        fuzzer_process = subprocess.Popen(fuzzer_command, shell=True)
    except Exception as e:
        print(f"❌ Error al lanzar el fuzzer: {e}")
        continue

    # Esperar el tiempo definido para la sesión
    print(f"⏳ Esperando {duracion_sesion} segundos de ejecución...")
    time.sleep(duracion_sesion)

    # --- 8. Matar el proceso del fuzzer --- #
    print("🚝 Matando proceso afl-fuzz...")
    subprocess.run("ps aux | grep afl-fuzz | grep -v grep | awk '{print $2}' | xargs -r kill -9", shell=True)

    # --- 9. Detener el servidor remoto --- #
    print("🚝 Deteniendo servidor remoto...")
    try:
        kill_server_cmd = (
            f"ssh {REMOTE_USER}@{REMOTE_IP} "
            "\"pwd && ps aux | grep servidor.py | grep -v grep | awk '{print \\$2}' | xargs -r kill -9\""
        )
        subprocess.run(kill_server_cmd, shell=True)
        print("✅ Servidor remoto detenido.")
    except Exception as e:
        print(f"⚠️  Error al detener servidor: {e}")

    # --- 10. Detener el monitoreo remoto --- #
    print("🚝 Deteniendo monitoreo remoto...")
    try:
        stop_monitor_cmd = f"ssh {REMOTE_USER}@{REMOTE_IP} \"pwd && pkill -f monitoreo.py\""
        subprocess.run(stop_monitor_cmd, shell=True)
        print("✅ Monitoreo detenido.")
    except Exception as e:
        print(f"⚠️  Error al detener monitoreo: {e}")
    
    # --- 11. Copiar logs desde la Raspberry al host local y procesarlos --- #
    print("📥 Copiando logs desde la Raspberry al host local...")
    try:
        # Definir rutas remotas y locales para los logs
        fuzzing_remote = f"{REMOTE_USER}@{REMOTE_IP}:{REMOTE_DIR}/Logs/FuzzingRasberry/{programa}/sesion_{sesion_actual}.txt"
        rendimiento_remote = f"{REMOTE_USER}@{REMOTE_IP}:{REMOTE_DIR}/Logs/MonitoreoRaspy/{programa}/sesion_{sesion_actual}.txt"
        fuzzing_local = os.path.join(LOGS_DIR, "FuzzingRasberry", programa, f"sesion_{sesion_actual}.txt")
        rendimiento_local = os.path.join(LOGS_DIR, "rendimientoRasberry", programa, f"sesion_{sesion_actual}.txt")

        # Copiar los archivos mediante scp
        subprocess.run(["scp", fuzzing_remote, fuzzing_local])
        subprocess.run(["scp", rendimiento_remote, rendimiento_local])

        print("✅ Logs copiados correctamente.")

        # Procesar el log de fuzzing con el script correspondiente
        print("🧪 Procesando los logs copiados...")
        subprocess.run(["python3", PROCESAR_SCRIPT, fuzzing_local, programa, str(sesion_actual)])
        print("✅ Logs de fuzzing procesados correctamente.")

        # Volcar el log de rendimiento en la base de datos utilizando otro script
        print("📊 Volcando log de rendimiento en la base de datos...")
        subprocess.run(["python3", VOLCAR_SCRIPT, rendimiento_local, programa, str(sesion_actual)])
        print("✅ Log de rendimiento volcado correctamente.")
    except Exception as e:
        print(f"⚠️  Error al copiar o procesar los logs: {e}")

# Finalizar todas las iteraciones
print("\n✅ Todas las iteraciones han terminado.")

# ---------------------- GENERACIÓN DE PARQUET Y DASHBOARD ---------------------- #

# Ruta absoluta al script parquet.py
parquet_script = os.path.join("DashBoard", "parquet.py")

print("\n📦 Ejecutando exportación a Parquet por programa...")
resultado = subprocess.run(["python3", parquet_script])

if resultado.returncode != 0:
    print("❌ Error al generar los archivos Parquet.")
else:
    print("✅ Archivos Parquet generados correctamente.")

# Lanzar el dashboard
dashboard_script = os.path.join("DashBoard", "Dashboard.py")
print("📊 Lanzando dashboard interactivo con Streamlit...")
subprocess.run(["streamlit", "run", dashboard_script])

