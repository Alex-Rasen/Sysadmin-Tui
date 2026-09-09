#!/bin/bash
set -e

echo "=== Instalador de SysAdmin TUI ==="
echo ""

# Verificar Python 3.10+
PYTHON_BIN=$(command -v python3 || command -v python)
if [ -z "$PYTHON_BIN" ]; then
    echo "Error: No se encontro Python 3. Instale Python 3.10 o superior."
    exit 1
fi

PY_VERSION=$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo $PY_VERSION | cut -d. -f1)
MINOR=$(echo $PY_VERSION | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
    echo "Error: Se requiere Python 3.10 o superior. Version actual: $PY_VERSION"
    exit 1
fi

# Directorio de instalacion
INSTALL_DIR="/opt/sysadmin-tui"
VENV_DIR="$INSTALL_DIR/venv"
CONFIG_DIR="/etc/sysadmin-tui"
LOG_DIR="/var/log/sysadmin-tui"
BIN_LINK="/usr/local/bin/sysadmin-tui"

echo "Directorio de instalacion: $INSTALL_DIR"
echo "Directorio de configuracion: $CONFIG_DIR"
echo "Directorio de logs: $LOG_DIR"
echo ""

# Crear directorios
echo "Creando directorios..."
sudo mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR"
sudo chown "$USER:$(id -gn)" "$INSTALL_DIR"

# Copiar codigo fuente (asumimos que el script se ejecuta desde la raiz del proyecto)
echo "Copiando archivos del proyecto..."
if [ -f "pyproject.toml" ]; then
    sudo cp -r . "$INSTALL_DIR/"
    sudo chown -R "$USER:$(id -gn)" "$INSTALL_DIR"
else
    echo "Error: No se encontro pyproject.toml en el directorio actual."
    echo "Ejecute este script desde la raiz del proyecto sysadmin-tui."
    exit 1
fi

# Crear entorno virtual
echo "Creando entorno virtual..."
cd "$INSTALL_DIR"
$PYTHON_BIN -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Instalar dependencias
echo "Instalando dependencias..."
pip install --upgrade pip
pip install .

# Crear enlace simbolico
echo "Creando enlace simbolico en $BIN_LINK"
sudo ln -sf "$VENV_DIR/bin/sysadmin-tui" "$BIN_LINK"

# Copiar configuracion de ejemplo si no existe
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo "Copiando configuracion de ejemplo a $CONFIG_DIR/config.yaml"
    sudo cp config.example.yaml "$CONFIG_DIR/config.yaml"
else
    echo "Ya existe $CONFIG_DIR/config.yaml, no se sobrescribe"
fi

# Ajustar permisos de directorio de logs
sudo chown -R "$USER:$(id -gn)" "$LOG_DIR"

# Desactivar entorno virtual
deactivate

echo ""
echo "Instalacion completada exitosamente."
echo "Puede ejecutar la aplicacion con el comando: sysadmin-tui"
echo "Para configurar, edite $CONFIG_DIR/config.yaml"
echo "Para desinstalar, ejecute: sudo rm -rf $INSTALL_DIR $CONFIG_DIR $LOG_DIR $BIN_LINK"
