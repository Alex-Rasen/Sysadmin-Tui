"""
Funciones de deteccion del sistema y servicios.
"""
import subprocess
import shutil
import os
import platform
from typing import Optional, List, Dict


def detect_distro() -> str:
    """Detecta la distribucion Linux (ubuntu, debian, centos, etc.)."""
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.strip().split("=")[1].strip('"').strip("'")
    return "unknown"


def get_package_manager() -> str:
    """Devuelve el gestor de paquetes principal."""
    distro = detect_distro()
    if distro in ["ubuntu", "debian", "linuxmint", "pop"]:
        return "apt"
    elif distro in ["centos", "rhel", "fedora", "rocky", "almalinux"]:
        return "dnf" if distro == "fedora" else "yum"
    elif distro in ["opensuse", "sles"]:
        return "zypper"
    elif distro in ["arch", "manjaro"]:
        return "pacman"
    else:
        return "unknown"


def detect_container_runtime() -> Optional[str]:
    """Detecta el runtime de contenedores disponible (docker o podman)."""
    if shutil.which("docker"):
        return "docker"
    elif shutil.which("podman"):
        return "podman"
    return None


def detect_web_server() -> Optional[str]:
    """Detecta el servidor web instalado."""
    for name in ["nginx", "apache2", "httpd", "caddy"]:
        if shutil.which(name):
            return name
    return None


def service_is_active(service_name: str) -> bool:
    """Comprueba si un servicio systemd esta activo."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "--quiet", service_name],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def service_status(service_name: str) -> str:
    """Devuelve estado de un servicio."""
    try:
        result = subprocess.run(
            ["systemctl", "status", service_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)


def list_active_services() -> List[Dict[str, str]]:
    """Devuelve servicios systemd activos como registros aptos para tablas."""
    try:
        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--state=active",
                "--no-legend",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return []
    if result.returncode != 0:
        return []

    services = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 4:
            continue
        unit, load, active, sub = parts[:4]
        description = parts[4] if len(parts) > 4 else ""
        services.append(
            {
                "unit": unit,
                "load": load,
                "active": active,
                "sub": sub,
                "description": description,
            }
        )
    return services


def get_ip_addresses() -> List[str]:
    """Devuelve lista de direcciones IP del sistema (sin loopback)."""
    import socket
    import fcntl
    import struct
    import array

    ifname_list = []
    try:
        ifconf = array.array('B', bytes(4096))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ifconf_bytes = fcntl.ioctl(sock.fileno(), 0x8912, ifconf)  # SIOCGIFCONF
        sock.close()
        ifconf = array.array('B', ifconf_bytes)
        offset = 0
        while offset < len(ifconf):
            ifreq = ifconf[offset:offset + 40]
            name = ifreq[:16].split(b'\0', 1)[0].decode()
            addr = socket.inet_ntoa(ifreq[20:24])
            if not addr.startswith("127."):
                ifname_list.append(f"{name}: {addr}")
            offset += 40
    except Exception:
        # Fallback: usar hostname -I
        result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
        if result.returncode == 0:
            ifname_list = result.stdout.strip().split()
    return ifname_list


def get_routes() -> str:
    """Devuelve la tabla de enrutamiento."""
    result = subprocess.run(["ip", "route"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else result.stderr


def get_dns_servers() -> str:
    """Devuelve servidores DNS configurados."""
    if os.path.exists("/etc/resolv.conf"):
        with open("/etc/resolv.conf", "r") as f:
            lines = [line.strip() for line in f if line.startswith("nameserver")]
            return "\n".join(lines) if lines else "Sin servidores DNS configurados"
    return "Archivo /etc/resolv.conf no encontrado"


def list_interfaces() -> str:
    """Lista interfaces de red."""
    result = subprocess.run(["ip", "-brief", "address"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else result.stderr
