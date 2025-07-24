import re
import ipaddress
import subprocess
import os
import getpass
from utils.config_db import get_connection

# Dispositivo seleccionado (variable global)
dispositivo_actual = {
    "id": None,
    "nombre": None,
    "ip": None,
    "usuario": None,
    "password": None,
    "arquitectura": None
}

def mostrar_menu():
    print("\n=== MENÚ DE DISPOSITIVOS ===")
    print("1. Ver dispositivos")
    print("2. Registrar nuevo dispositivo")
    print("3. Seleccionar dispositivo")
    print("4. Borrar dispositivo")
    print("5. Salir")

def ver_dispositivos():
    conn = get_connection()
    if conn is None:
        print("❌ No se pudo conectar a la base de datos.")
        return

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM dispositivos")
        rows = cursor.fetchall()

        if not rows:
            print("⚠️ No hay dispositivos registrados.")
            return

        print("\n📋 Dispositivos registrados:")
        for row in rows:
            print(f"ID: {row['id']} | Nombre: {row['nombre']} | IP: {row['ip']} | Usuario: {row['usuario']} | Arquitectura: {row['arquitectura']}")

    except Exception as e:
        print(f"❌ Error al obtener dispositivos: {e}")
    finally:
        conn.close()

def registrar_dispositivo():
    conn = get_connection()
    if conn is None:
        print("❌ No se pudo conectar a la base de datos.")
        return

    try:
        # Nombre
        while True:
            nombre = input("Nombre del dispositivo: ").strip()
            if not nombre:
                print("⚠️ El nombre no puede estar vacío.")
            elif not re.match(r'^[\w\-]+$', nombre):
                print("⚠️ Solo se permiten letras, números, guiones y guiones bajos.")
            else:
                break

        # IP
        while True:
            ip = input("Dirección IP: ").strip()
            try:
                ipaddress.ip_address(ip)
                break
            except ValueError:
                print("⚠️ IP inválida. Introduce una dirección IPv4 válida (ej. 192.168.1.10).")

        # Usuario
        while True:
            usuario = input("Usuario SSH: ").strip()
            if not usuario:
                print("⚠️ El usuario no puede estar vacío.")
            else:
                break

        # Password (oculto al escribir)
        while True:
            password = getpass.getpass("Password SSH: ").strip()
            if not password:
                print("⚠️ El password no puede estar vacío.")
            else:
                break

        # Arquitectura
        arquitecturas_validas = ["arm", "x86", "x86_64"]
        while True:
            arquitectura = input("Arquitectura (arm/x86/x86_64): ").strip().lower()
            if arquitectura not in arquitecturas_validas:
                print(f"⚠️ Arquitectura inválida. Opciones válidas: {', '.join(arquitecturas_validas)}")
            else:
                break

        # Comprobar conexión SSH y copiar clave
        print("🔐 Comprobando conexión SSH y configurando clave pública...")

        ssh_dir = os.path.expanduser("~/.ssh")
        id_rsa = os.path.join(ssh_dir, "id_rsa")
        if not os.path.isfile(id_rsa):
            print("🔧 Generando nueva clave SSH...")
            subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "2048", "-f", id_rsa, "-N", ""])

        ssh_copy_cmd = f"sshpass -p '{password}' ssh-copy-id -o StrictHostKeyChecking=no {usuario}@{ip}"
        resultado = subprocess.run(ssh_copy_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if resultado.returncode != 0:
            print("❌ No se pudo establecer la conexión SSH ni instalar la clave pública.")
            print(resultado.stderr.decode())
            return

        # Insertar en la base de datos
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dispositivos")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("ALTER TABLE dispositivos AUTO_INCREMENT = 1")

        cursor.execute(
            "INSERT INTO dispositivos (nombre, ip, usuario, password, arquitectura) VALUES (%s, %s, %s, %s, %s)",
            (nombre, ip, usuario, password, arquitectura)
        )
        conn.commit()
        print("✅ Dispositivo registrado y acceso SSH configurado correctamente.")

    except Exception as e:
        print(f"❌ Error al registrar dispositivo: {e}")
    finally:
        conn.close()

def seleccionar_dispositivo():
    conn = get_connection()
    if conn is None:
        print("❌ No se pudo conectar a la base de datos.")
        return

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM dispositivos")
        rows = cursor.fetchall()

        if not rows:
            print("⚠️ No hay dispositivos registrados.")
            return

        print("\n📋 Dispositivos disponibles:")
        for row in rows:
            print(f"[{row['id']}] {row['nombre']} - {row['ip']}")

        seleccion = input("Ingrese el ID del dispositivo que desea usar: ").strip()
        seleccionado = next((d for d in rows if str(d["id"]) == seleccion), None)

        if seleccionado:
            # Aquí modificamos el diccionario existente clave a clave
            dispositivo_actual["id"] = seleccionado["id"]
            dispositivo_actual["nombre"] = seleccionado["nombre"]
            dispositivo_actual["ip"] = seleccionado["ip"]
            dispositivo_actual["usuario"] = seleccionado["usuario"]
            dispositivo_actual["password"] = seleccionado["password"]
            dispositivo_actual["arquitectura"] = seleccionado["arquitectura"]

            print(f"✅ Dispositivo '{dispositivo_actual['nombre']}' seleccionado.")
        else:
            print("❌ ID inválido.")
    except Exception as e:
        print(f"❌ Error al seleccionar dispositivo: {e}")
    finally:
        conn.close()

def borrar_dispositivo():
    conn = get_connection()
    if conn is None:
        print("❌ No se pudo conectar a la base de datos.")
        return

    try:
        ver_dispositivos()
        id_str = input("Ingrese el ID del dispositivo que desea borrar: ").strip()
        if not id_str.isdigit():
            print("❌ El ID debe ser un número.")
            return

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE id = %s", (id_str,))
        existe = cursor.fetchone()[0]
        if existe == 0:
            print("❌ No existe ningún dispositivo con ese ID.")
            return

        confirmacion = input("⚠️ ¿Estás seguro de que quieres borrar este dispositivo? (s/n): ").strip().lower()
        if confirmacion != "s":
            print("❌ Cancelado por el usuario.")
            return

        cursor.execute("DELETE FROM dispositivos WHERE id = %s", (id_str,))
        conn.commit()
        print("✅ Dispositivo borrado correctamente.")

    except Exception as e:
        print(f"❌ Error al borrar dispositivo: {e}")
    finally:
        conn.close()

def lanzar_menu_dispositivos():
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción [1-5]: ").strip()
        if opcion == "1":
            ver_dispositivos()
        elif opcion == "2":
            registrar_dispositivo()
        elif opcion == "3":
            seleccionar_dispositivo()
            if dispositivo_actual["ip"]:
                break  # Salir del menú si se ha seleccionado correctamente
        elif opcion == "4":
            borrar_dispositivo()
        elif opcion == "5":
            break
        else:
            print("❌ Opción no válida.")
