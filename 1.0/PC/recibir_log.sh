#!/bin/bash

# === CONFIGURACIÓN ===
USUARIO_REMOTO="markel"
IP_REMOTA="172.16.124.103"
ARCHIVO_REMOTO="demo_log.txt"
RUTA_REMOTA="/home/markel/Documents/Pruebas/Versions/1.0/Logs"

# Ruta local de destino (relativa a este script)
DESTINO_LOCAL="$(dirname "$0")/datosFuzzing"
ARCHIVO_LOCAL="${DESTINO_LOCAL}/${ARCHIVO_REMOTO}"

# === INICIO ===
echo "🔄 Iniciando transferencia de archivo desde la Raspberry Pi..."

# Verificar o crear la carpeta de destino
if [ ! -d "$DESTINO_LOCAL" ]; then
    echo "📁 El directorio de destino no existe. Creándolo..."
    mkdir -p "$DESTINO_LOCAL"
    if [ $? -ne 0 ]; then
        echo "❌ Error: No se pudo crear el directorio de destino."
        exit 1
    fi
fi

# Copiar el archivo usando SCP
echo "📡 Conectando a ${USUARIO_REMOTO}@${IP_REMOTA}..."
scp "${USUARIO_REMOTO}@${IP_REMOTA}:${RUTA_REMOTA}/${ARCHIVO_REMOTO}" "$ARCHIVO_LOCAL"

# Comprobación final
if [ $? -eq 0 ]; then
    echo "✅ Archivo recibido correctamente y guardado como:"
    echo "   $ARCHIVO_LOCAL"
else
    echo "❌ Error al copiar el archivo. Verifica la conexión o la ruta."
    exit 1
fi
