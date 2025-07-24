#!/usr/bin/env python3
import os
import sys
import time
import psutil
from datetime import datetime

def get_temp():
    """Intenta leer la temperatura del sistema desde los sensores estándar."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
        return f"{temp:.1f} ºC"
    except:
        return "N/A"

def get_net_usage(initial):
    """Calcula la diferencia de uso de red en bytes y devuelve valores legibles."""
    current = psutil.net_io_counters()
    recv = (current.bytes_recv - initial.bytes_recv) / (1024 ** 3)
    sent = (current.bytes_sent - initial.bytes_sent) / (1024 ** 3)
    return f"Recibidos={recv:.2f} GB, Enviados={sent:.2f} GB"

# Verificación de argumentos
if len(sys.argv) < 4:
    print("Uso: python3 monitoreo.py <programa> <sesion> <duracion_segundos>")
    sys.exit(1)

programa = sys.argv[1]
sesion = int(sys.argv[2])
duracion = int(sys.argv[3])

# Ruta base absoluta
base_dir = "/home/markel/Documents/automaticoTest/Logs/MonitoreoRaspy"
log_dir = os.path.join(base_dir, programa)
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"sesion_{sesion}.txt")

print(f"[INFO] Iniciando monitoreo para {programa}, sesión {sesion}")
print(f"[INFO] Log: {log_file}")

# Registrar uso inicial de red
net_start = psutil.net_io_counters()

try:
    with open(log_file, "w") as f:
        f.write(f"📊 Monitoreo iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        inicio = time.time()

        while time.time() - inicio < duracion:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            temp = get_temp()
            net = get_net_usage(net_start)

            f.write(f"--- {timestamp} ---\n")
            f.write(f"CPU: {cpu:.1f}%\n")
            f.write(f"Memoria: {mem:.1f}% usada\n")
            f.write(f"Disco: {disk:.1f}% usado\n")
            f.write(f"Temperatura CPU: {temp}\n")
            f.write(f"Red: {net}\n\n")
            f.flush()

    print("[INFO] Monitoreo finalizado correctamente.")

except Exception as e:
    print(f"[ERROR] {e}")
