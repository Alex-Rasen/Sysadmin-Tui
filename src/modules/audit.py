"""
Modulo de registro y auditoria.
"""
from src.modules.base import BaseModule, ModuleRegistry


class Module(BaseModule):
    display_name = "Auditoria"
    name = "audit"
    actions = {
        "list_failed_logins": {"description": "Listar intentos de login fallidos", "params": {}},
        "list_audit_log": {"description": "Ver log de auditoria del sistema", "params": {"lines": "int?"}},
        "enable_auditd": {"description": "Activar auditd", "params": {}},
    }

    def render_summary(self) -> str:
        return "Modulo de auditoria"

    def action_list_failed_logins(self) -> str:
        return self.run_command("grep 'Failed password' /var/log/auth.log | tail -20")[1] or "No hay registros"

    def action_list_audit_log(self, lines=50) -> str:
        return self.run_command(f"tail -n {lines} /var/log/syslog")[1] or "No hay syslog"

    def action_enable_auditd(self) -> str:
        return self.run_command("systemctl enable --now auditd", use_sudo=True)[2] or "auditd activado"


ModuleRegistry.register(Module)
