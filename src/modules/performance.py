"""
Modulo de rendimiento y tuning.
"""
from src.modules.base import BaseModule, ModuleRegistry


class Module(BaseModule):
    display_name = "Rendimiento"
    name = "performance"
    actions = {
        "sysctl_list": {"description": "Listar parametros sysctl", "params": {}},
        "sysctl_set": {"description": "Establecer parametro sysctl", "params": {"key": "str", "value": "str"}},
        "swap_info": {"description": "Informacion de swap", "params": {}},
        "top": {"description": "Monitor de procesos en tiempo real (top)", "params": {}},
    }

    def render_summary(self) -> str:
        return "Modulo de rendimiento"

    def action_sysctl_list(self) -> str:
        return self.run_command("sysctl -a")[1] or "No se pudo obtener sysctl"

    def action_sysctl_set(self, key, value) -> str:
        code, out, err = self.run_command(f"sysctl -w {key}={value}", use_sudo=True)
        return out if code == 0 else f"Error: {err}"

    def action_swap_info(self) -> str:
        return self.run_command("swapon --show")[1] or "No hay swap activo"

    def action_top(self) -> str:
        # Ejecutar top en modo batch una sola iteracion
        return self.run_command("top -bn1 | head -20")[1]


ModuleRegistry.register(Module)
