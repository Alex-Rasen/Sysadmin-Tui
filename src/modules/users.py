"""
Modulo de gestion de usuarios y permisos.
"""
from src.modules.base import BaseModule, ModuleRegistry


class Module(BaseModule):
    display_name = "Usuarios y Permisos"
    name = "users"
    actions = {
        "list_users": {"description": "Listar usuarios del sistema", "params": {}},
        "add_user": {"description": "Crear usuario", "params": {"username": "str", "shell": "str?"}},
        "delete_user": {"description": "Eliminar usuario", "params": {"username": "str"}},
        "list_sudoers": {"description": "Listar sudoers", "params": {}},
        "add_sudoer": {"description": "Agregar usuario a sudoers", "params": {"username": "str"}},
    }

    def render_summary(self) -> str:
        return f"Usuarios totales: {len(self._get_users())}"

    def _get_users(self):
        with open("/etc/passwd", "r") as f:
            return [line.split(":")[0] for line in f if int(line.split(":")[2]) >= 1000]

    def action_list_users(self) -> str:
        users = self._get_users()
        return "\n".join(users) if users else "No hay usuarios normales"

    def action_add_user(self, username, shell="/bin/bash") -> str:
        code, out, err = self.run_command(f"useradd -m -s {shell} {username}", use_sudo=True)
        return out if code == 0 else f"Error: {err}"

    def action_delete_user(self, username) -> str:
        code, out, err = self.run_command(f"userdel -r {username}", use_sudo=True)
        return out if code == 0 else f"Error: {err}"

    def action_list_sudoers(self) -> str:
        return self.run_command("cat /etc/sudoers")[1] or "No se puede leer sudoers"

    def action_add_sudoer(self, username) -> str:
        code, out, err = self.run_command(f"usermod -aG sudo {username}", use_sudo=True)
        return "Usuario agregado al grupo sudo" if code == 0 else f"Error: {err}"


ModuleRegistry.register(Module)
