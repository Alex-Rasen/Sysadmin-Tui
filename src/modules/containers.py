"""
Modulo de gestion de contenedores (Docker/Podman).
"""
from typing import Optional
from src.modules.base import BaseModule, ModuleRegistry
from src.utils.system import detect_container_runtime


class Module(BaseModule):
    display_name = "Contenedores"
    name = "containers"
    actions = {
        "list": {"description": "Listar contenedores", "params": {"all": "bool"}},
        "start": {"description": "Iniciar contenedor", "params": {"name": "str"}},
        "stop": {"description": "Detener contenedor", "params": {"name": "str"}},
        "restart": {"description": "Reiniciar contenedor", "params": {"name": "str"}},
        "logs": {"description": "Ver logs de contenedor", "params": {"name": "str"}},
        "images": {"description": "Listar imagenes", "params": {}},
        "prune": {"description": "Eliminar contenedores detenidos", "params": {}},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtime = self.module_config.get("runtime", "auto")
        if self.runtime == "auto":
            self.runtime = detect_container_runtime() or "docker"

    def render_summary(self) -> str:
        if not self.runtime:
            return "No se detecto Docker ni Podman instalado."
        # Plantilla cruda para que Docker reciba \t literal y {{...}}
        fmt = r"table {{.Names}}\t{{.Status}}"
        cmd = f"{self.runtime} ps --format '{fmt}'"
        code, out, err = self.run_command(cmd)
        if code == 0:
            return f"Contenedores activos ({self.runtime}):\n{out}"
        return f"Error al obtener contenedores: {err}"

    def action_list(self, all=False) -> str:
        flag = " -a" if all else ""
        fmt = r"table {{.Names}}\t{{.Image}}\t{{.Status}}"
        cmd = f"{self.runtime} ps{flag} --format '{fmt}'"
        code, out, err = self.run_command(cmd)
        return out if code == 0 else f"Error: {err}"

    def action_start(self, name) -> str:
        code, out, err = self.run_command(f"{self.runtime} start {name}")
        return out if code == 0 else f"Error: {err}"

    def action_stop(self, name) -> str:
        code, out, err = self.run_command(f"{self.runtime} stop {name}")
        return out if code == 0 else f"Error: {err}"

    def action_restart(self, name) -> str:
        code, out, err = self.run_command(f"{self.runtime} restart {name}")
        return out if code == 0 else f"Error: {err}"

    def action_logs(self, name) -> str:
        code, out, err = self.run_command(f"{self.runtime} logs --tail 50 {name}")
        return out if code == 0 else f"Error: {err}"

    def action_images(self) -> str:
        fmt = r"table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"
        cmd = f"{self.runtime} images --format '{fmt}'"
        code, out, err = self.run_command(cmd)
        return out if code == 0 else f"Error: {err}"

    def action_prune(self) -> str:
        code, out, err = self.run_command(f"{self.runtime} container prune -f")
        return out if code == 0 else f"Error: {err}"


ModuleRegistry.register(Module)
