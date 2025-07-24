#!/usr/bin/env python3
import sys
import os
import subprocess
import socket
import codecs
import datetime
import tempfile

# Verificar que se pasaron los dos argumentos
if len(sys.argv) < 3:
    print("Uso: python3 servidor.py <programa> <sesion>")
    sys.exit(1)

programa = sys.argv[1]
sesion = int(sys.argv[2])

# Ruta al binario a ejecutar
BINARIO = f"./{programa}"

# Crear carpeta de logs
LOG_DIR = f"Logs/FuzzingRasberry/{programa}"
os.makedirs(LOG_DIR, exist_ok=True)

# Ruta del archivo de log de la sesión
LOG_FILE = os.path.join(LOG_DIR, f"sesion_{sesion}.txt")

print("BINARIO configurado como:", BINARIO)
print("LOG_FILE configurado como:", LOG_FILE)

def ejecutar_binario(input_data):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(input_data)
            tmp.flush()
            tmp_name = tmp.name

        proceso = subprocess.run(
            [BINARIO, tmp_name],
            capture_output=True,
            timeout=5
        )

        exit_code = proceso.returncode if proceso.returncode >= 0 else -proceso.returncode

        os.remove(tmp_name)
        return exit_code

    except subprocess.TimeoutExpired:
        return 124
    except Exception as e:
        print(f"Error al ejecutar el binario: {e}", file=sys.stderr)
        return 125


def guardar_log(input_data, exit_code):
    escaped_input = codecs.escape_encode(input_data)[0].decode('ascii')
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"Input: {escaped_input}\n")
        log.write(f"Código de salida: {exit_code}\n")
        log.write("--------------------------\n")

def log_connection_closed():
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"Conexión cerrada: {now}\n")
        log.write("--------------------------\n")

def start_server(host='0.0.0.0', port=1234):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor escuchando en {host}:{port}...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Conexión establecida con {client_address}")

            data = client_socket.recv(1024)
            if data:
                print(f"Input recibido: {data}")
                exit_code = ejecutar_binario(data)
                guardar_log(data, exit_code)
            try:
                client_socket.sendall(f"{exit_code}".encode('latin-1'))
                client_socket.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                print("Error al cerrar conexión correctamente:", e)
            finally:
                client_socket.close()
            log_connection_closed()

    except KeyboardInterrupt:
        print("Servidor detenido.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # Limpiar el archivo de log de la sesión al iniciar
    open(LOG_FILE, "wb").close()
    inicio = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"Servidor iniciado: {inicio}\n")
        log.write("--------------------------\n")

    start_server()
