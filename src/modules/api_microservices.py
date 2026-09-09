"""
Modulo de APIs y microservicios.
"""
import json
from src.modules.base import BaseModule, ModuleRegistry


class Module(BaseModule):
    display_name = "APIs y Microservicios"
    name = "api_microservices"
    actions = {
        "healthcheck": {"description": "Verificar salud de un endpoint", "params": {"url": "str", "method": "str?"}},
        "list_endpoints": {"description": "Listar endpoints configurados", "params": {}},
    }

    def render_summary(self) -> str:
        return "Modulo de APIs y microservicios"

    def action_healthcheck(self, url, method="GET") -> str:
        import urllib.request
        try:
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return f"HTTP {resp.status} - OK"
        except Exception as e:
            return f"Error: {e}"

    def action_list_endpoints(self) -> str:
        # Leer de configuracion endpoints definidos
        endpoints = self.module_config.get("endpoints", [])
        if not endpoints:
            return "No hay endpoints configurados. Agrega 'endpoints' en la configuracion del modulo."
        return "\n".join(f"{ep.get('name', 'sin nombre')}: {ep.get('url', '')}" for ep in endpoints)


ModuleRegistry.register(Module)
