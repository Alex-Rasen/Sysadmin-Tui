"""
Modulo de actualizaciones del sistema.
"""
from src.modules.base import BaseModule, ModuleRegistry
from src.utils.system import get_package_manager


class Module(BaseModule):
    display_name = "Actualizaciones"
    name = "updates"
    actions = {
        "check": {"description": "Comprobar actualizaciones disponibles", "params": {}},
        "list_updates": {"description": "Listar paquetes actualizables", "params": {}},
        "upgrade": {"description": "Aplicar actualizaciones", "params": {}},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pkg_manager = get_package_manager()
        if self.pkg_manager == "apt":
            self.update_cmd = "apt update"
            self.list_cmd = "apt list --upgradable"
            self.upgrade_cmd = "apt upgrade -y"
        elif self.pkg_manager in ["dnf", "yum"]:
            self.update_cmd = f"{self.pkg_manager} check-update"
            self.list_cmd = f"{self.pkg_manager} list updates"
            self.upgrade_cmd = f"{self.pkg_manager} upgrade -y"
        elif self.pkg_manager == "zypper":
            self.update_cmd = "zypper refresh"
            self.list_cmd = "zypper list-updates"
            self.upgrade_cmd = "zypper update -y"
        elif self.pkg_manager == "pacman":
            self.update_cmd = "pacman -Sy"
            self.list_cmd = "pacman -Qu"
            self.upgrade_cmd = "pacman -Su --noconfirm"
        else:
            self.pkg_manager = "unknown"

    def render_summary(self) -> str:
        if self.pkg_manager == "unknown":
            return "Gestor de paquetes no soportado"
        return f"Gestor de paquetes: {self.pkg_manager}"

    def action_check(self) -> str:
        if self.pkg_manager == "unknown":
            return "Gestor no soportado"
        return self.run_command(self.update_cmd, use_sudo=True)[2] or "Comprobacion realizada"

    def action_list_updates(self) -> str:
        if self.pkg_manager == "unknown":
            return "Gestor no soportado"
        return self.run_command(self.list_cmd)[1] or "No hay actualizaciones"

    def action_upgrade(self) -> str:
        if self.pkg_manager == "unknown":
            return "Gestor no soportado"
        return self.run_command(self.upgrade_cmd, use_sudo=True)[2] or "Actualizacion completada"


ModuleRegistry.register(Module)
