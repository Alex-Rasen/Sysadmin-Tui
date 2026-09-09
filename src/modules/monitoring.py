"""
Modulo de supervision y alertas.
"""
from src.modules.base import BaseModule, ModuleRegistry
from src.utils.formatters import format_bytes


class Module(BaseModule):
    display_name = "Supervision"
    name = "monitoring"
    actions = {
        "cpu": {"description": "Uso de CPU", "params": {}},
        "memory": {"description": "Uso de memoria", "params": {}},
        "disk": {"description": "Uso de disco", "params": {}},
        "network": {"description": "Estadisticas de red", "params": {}},
        "processes": {"description": "Procesos principales", "params": {"count": "int?"}},
    }

    def render_summary(self) -> str:
        return "Modulo de supervision"

    def action_cpu(self) -> str:
        return self.run_command("top -bn1 | head -5")[1]

    def action_memory(self) -> str:
        return self.run_command("free -h")[1]

    def action_disk(self) -> str:
        return self.run_command("df -h")[1]

    def action_network(self) -> str:
        return self.run_command("ss -s")[1]

    def action_processes(self, count=10) -> str:
        return self.run_command(f"ps aux --sort=-%cpu | head -n {int(count)+1}")[1]


ModuleRegistry.register(Module)
