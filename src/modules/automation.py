"""
Modulo de automatizacion y scripting.
"""
from src.modules.base import BaseModule, ModuleRegistry


class Module(BaseModule):
    display_name = "Automatizacion"
    name = "automation"
    actions = {
        "list_cron": {"description": "Listar tareas cron", "params": {}},
        "add_cron": {"description": "Agregar tarea cron", "params": {"schedule": "str", "command": "str"}},
        "list_timers": {"description": "Listar timers de systemd", "params": {}},
        "run_script": {"description": "Ejecutar script", "params": {"path": "str"}},
    }

    def render_summary(self) -> str:
        return "Modulo de automatizacion"

    def action_list_cron(self) -> str:
        return self.run_command("crontab -l")[1] or "No hay tareas cron"

    def action_add_cron(self, schedule, command) -> str:
        # Anadir linea al crontab actual
        current = self.run_command("crontab -l")[1] or ""
        new_entry = f"{schedule} {command}\n"
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(current + new_entry)
            fname = f.name
        code, out, err = self.run_command(f"crontab {fname}")
        import os
        os.unlink(fname)
        return "Tarea agregada" if code == 0 else f"Error: {err}"

    def action_list_timers(self) -> str:
        return self.run_command("systemctl list-timers --no-pager")[1]

    def action_run_script(self, path) -> str:
        code, out, err = self.run_command(f"bash {path}")
        return out if code == 0 else f"Error: {err}"


ModuleRegistry.register(Module)
