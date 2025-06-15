#!/usr/bin/env python3
import os
import subprocess
import paramiko
import tkinter as tk
from tkinter import messagebox
from config import root, set_selected_device, get_selected_device
from config_db import get_connection, get_database_name

def open_dispositivos():
    root.withdraw()
    ventana_dis = tk.Toplevel()
    ventana_dis.title("Dispositivos")
    ventana_dis.geometry("300x250")

    btn_anadir = tk.Button(ventana_dis, text="Añadir", command=anadir_dispositivo)
    btn_anadir.pack(pady=5)

    btn_listar = tk.Button(ventana_dis, text="Listar Dispositivos", command=listar_dispositivos)
    btn_listar.pack(pady=5)

    btn_configurar = tk.Button(ventana_dis, text="Configurar", command=configurar_dispositivo)
    btn_configurar.pack(pady=5)

    btn_volver = tk.Button(ventana_dis, text="Volver", command=lambda: [ventana_dis.destroy(), root.deiconify()])
    btn_volver.pack(pady=5)

def anadir_dispositivo():
    global ventana
    ventana = tk.Toplevel()
    ventana.title("Añadir Dispositivo")
    ventana.geometry("350x500")

    lbl_nombre = tk.Label(ventana, text="Nombre de Referencia:")
    lbl_nombre.pack(pady=(10, 0))
    nombre_entry = tk.Entry(ventana, width=30)
    nombre_entry.pack()

    lbl_ip = tk.Label(ventana, text="IP:")
    lbl_ip.pack(pady=(10, 0))
    ip_entry = tk.Entry(ventana, width=30)
    ip_entry.pack()

    lbl_usuario = tk.Label(ventana, text="Usuario:")
    lbl_usuario.pack(pady=(10, 0))
    usuario_entry = tk.Entry(ventana, width=30)
    usuario_entry.pack()

    lbl_password = tk.Label(ventana, text="Password:")
    lbl_password.pack(pady=(10, 0))
    password_entry = tk.Entry(ventana, show="*", width=30)
    password_entry.pack()

    lbl_arquitectura = tk.Label(ventana, text="Arquitectura:")
    lbl_arquitectura.pack(pady=(10, 0))
    arquitectura_var = tk.StringVar(value="ARM-64")
    opciones = ["ARM-64", "ARM-32"]
    dropdown = tk.OptionMenu(ventana, arquitectura_var, *opciones)
    dropdown.config(width=10)
    dropdown.pack(pady=(0, 10))

    def guardar():
        nombre = nombre_entry.get().strip()
        ip = ip_entry.get().strip()
        usuario = usuario_entry.get().strip()
        password = password_entry.get().strip()
        arquitectura = arquitectura_var.get().strip()

        if not nombre or not ip or not usuario or not password:
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return

        conn = get_connection(get_database_name())
        if conn is None:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
            return

        cursor = conn.cursor()
        insert_query = """
        INSERT INTO dispositivos (nombre, ip, usuario, password, arquitectura)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(insert_query, (nombre, ip, usuario, password, arquitectura))
            conn.commit()
            messagebox.showinfo("Éxito", "Datos guardados correctamente en la base de datos")
        except Exception as e:
            messagebox.showerror("Error", f"Error al insertar en la base de datos:\n{e}")
        finally:
            cursor.close()
            conn.close()
            ventana.destroy()

    btn_guardar = tk.Button(ventana, text="Guardar", command=guardar)
    btn_guardar.pack(pady=5)

    btn_cancelar = tk.Button(ventana, text="Cancelar", command=ventana.destroy)
    btn_cancelar.pack(pady=5)

def listar_dispositivos():
    conn = get_connection(get_database_name())
    if conn is None:
        messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nombre, ip, usuario, password, arquitectura FROM dispositivos")
        dispositivos = cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Error", f"Error al consultar dispositivos:\n{e}")
        cursor.close()
        conn.close()
        return
    
    cursor.close()
    conn.close()

    if not dispositivos:
        messagebox.showinfo("Información", "No hay dispositivos registrados.")
        return

    ventana_list = tk.Toplevel()
    ventana_list.title("Listar Dispositivos")
    ventana_list.geometry("400x300")

    lbl_info = tk.Label(ventana_list, text="Seleccione un dispositivo:")
    lbl_info.pack(pady=10)

    listbox = tk.Listbox(ventana_list, width=50, height=10)
    listbox.pack(pady=5)

    dispositivos_data = []
    for disp in dispositivos:
        dispositivos_data.append(disp)
        listbox.insert(tk.END, f"{disp[1]} ({disp[2]})")

    def seleccionar_dispositivo():
        index = listbox.curselection()
        if not index:
            messagebox.showwarning("Advertencia", "Seleccione un dispositivo de la lista.")
            return
        
        idx = index[0]
        disp_seleccionado = dispositivos_data[idx]

        set_selected_device({
            "id": disp_seleccionado[0],
            "nombre": disp_seleccionado[1],
            "ip": disp_seleccionado[2],
            "usuario": disp_seleccionado[3],
            "password": disp_seleccionado[4],
            "arquitectura": disp_seleccionado[5]
        })
        print("DEBUG: asignando el dispositivo:", disp_seleccionado)
        messagebox.showinfo("Dispositivo seleccionado", 
            f"Has seleccionado: {disp_seleccionado[1]} ({disp_seleccionado[2]})")
        ventana_list.destroy()

    btn_seleccionar = tk.Button(ventana_list, text="Seleccionar", command=seleccionar_dispositivo)
    btn_seleccionar.pack(pady=5)

    btn_cerrar = tk.Button(ventana_list, text="Cerrar", command=ventana_list.destroy)
    btn_cerrar.pack(pady=5)

def configurar_dispositivo():
    dispositivo = get_selected_device()
    print("DEBUG: en configurar_dispositivo, dispositivo =", dispositivo)
    if not dispositivo:
        messagebox.showerror("Error", "No se ha seleccionado ningún dispositivo. Por favor, selecciona uno.")
        return

    ip = dispositivo["ip"]
    usuario = dispositivo["usuario"]
    password = dispositivo["password"]

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=ip, username=usuario, password=password, timeout=10)
        messagebox.showinfo("Conexión SSH", "Conexión realizada correctamente.")
    except Exception as e:
        messagebox.showerror("Conexión SSH", f"Error al conectar al dispositivo:\n{e}")
        return

    ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, mode=0o700)

    key_priv = os.path.join(ssh_dir, "id_ed25519")
    key_pub = key_priv + ".pub"

    if os.path.exists(key_priv) and os.path.exists(key_pub):
        messagebox.showinfo("Claves SSH", "Las claves por defecto ya existen en ~/.ssh.")
    else:
        try:
            subprocess.run(
                ["ssh-keygen", "-t", "ed25519", "-f", key_priv, "-C", "fuzzingKeys", "-N", ""],
                check=True
            )
            messagebox.showinfo("Claves SSH", "Par de claves generado correctamente en ~/.ssh.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Claves SSH", f"Error al generar las claves:\n{e}")
            ssh.close()
            return

    try:
        with open(key_pub, "r") as f:
            pub_key = f.read().strip()
    except Exception as e:
        messagebox.showerror("Claves SSH", f"Error al leer la clave pública:\n{e}")
        ssh.close()
        return

    remote_cmd = (
        'mkdir -p ~/.ssh && chmod 700 ~/.ssh && '
        'echo "{}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
    ).format(pub_key.replace('"', '\\"'))

    try:
        stdin, stdout, stderr = ssh.exec_command(remote_cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            messagebox.showinfo("Clave Pública", "Clave pública enviada y agregada correctamente.")
        else:
            err = stderr.read().decode().strip()
            messagebox.showerror("Clave Pública", f"Error al agregar la clave pública:\n{err}")
    except Exception as e:
        messagebox.showerror("Clave Pública", f"Error al ejecutar comando remoto:\n{e}")
    finally:
        ssh.close()
