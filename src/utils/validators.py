"""
Validadores para entradas de usuario.
"""
import ipaddress
import re


def validate_ip(ip: str) -> bool:
    """Valida direccion IP (v4 o v6)."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_port(port: str) -> bool:
    """Valida puerto TCP/UDP (1-65535)."""
    try:
        p = int(port)
        return 1 <= p <= 65535
    except ValueError:
        return False


def validate_path(path: str) -> bool:
    """Valida ruta de archivo absoluta."""
    return path.startswith("/") and len(path) > 1


def validate_hostname(hostname: str) -> bool:
    """Valida nombre de host."""
    pattern = re.compile(r"^[a-zA-Z0-9.-]+$")
    return bool(pattern.match(hostname)) and len(hostname) <= 255


def validate_username(username: str) -> bool:
    """Valida nombre de usuario Linux."""
    pattern = re.compile(r"^[a-z_][a-z0-9_-]*$")
    return bool(pattern.match(username)) and len(username) <= 32
