"""
Modulo de gestion de red.
"""
from src.modules.base import BaseModule, ModuleRegistry
from src.utils.system import get_ip_addresses, get_routes, get_dns_servers, list_interfaces


class Module(BaseModule):
    display_name = "Redes"
    name = "network"
    actions = {
        "info": {"description": "Informacion de red general", "params": {}},
        "interfaces": {"description": "Listar interfaces", "params": {}},
        "routes": {"description": "Mostrar tabla de rutas", "params": {}},
        "dns": {"description": "Mostrar servidores DNS", "params": {}},
        "edit_hosts": {"description": "Mostrar /etc/hosts", "params": {}},
        "ping": {"description": "Hacer ping a un host", "params": {"host": "str"}},
        "traceroute": {"description": "Trazar ruta a un host", "params": {"host": "str"}},
    }

    def render_summary(self) -> str:
        ips = get_ip_addresses()
        return f"IPs del sistema:\n" + "\n".join(ips) if ips else "Sin IPs detectadas"

    def action_info(self) -> str:
        return self.render_summary() + "\n\n" + self.action_routes() + "\n\nDNS:\n" + self.action_dns()

    def action_interfaces(self) -> str:
        return list_interfaces()

    def action_routes(self) -> str:
        return get_routes()

    def action_dns(self) -> str:
        return get_dns_servers()

    def action_edit_hosts(self) -> str:
        with open("/etc/hosts", "r") as f:
            return f.read()

    def action_ping(self, host) -> str:
        code, out, err = self.run_command(f"ping -c 4 {host}")
        return out if code == 0 else f"Error: {err}"

    def action_traceroute(self, host) -> str:
        code, out, err = self.run_command(f"traceroute {host}")
        return out if code == 0 else f"Error: {err}"


ModuleRegistry.register(Module)
