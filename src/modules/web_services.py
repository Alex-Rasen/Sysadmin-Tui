"""
Modulo de servicios web (Nginx, Apache, Caddy).
"""
from src.modules.base import BaseModule, ModuleRegistry
from src.utils.system import detect_web_server, service_is_active, service_status


class Module(BaseModule):
    display_name = "Servicios Web"
    name = "web_services"
    actions = {
        "status": {"description": "Estado del servidor web", "params": {}},
        "restart": {"description": "Reiniciar servidor web", "params": {"service": "str?"}},
        "reload": {"description": "Recargar configuracion", "params": {"service": "str?"}},
        "config_check": {"description": "Verificar configuracion", "params": {"service": "str?"}},
        "logs_error": {"description": "Ver logs de error", "params": {"lines": "int?"}},
        "logs_access": {"description": "Ver logs de acceso", "params": {"lines": "int?"}},
        "cert_renew": {"description": "Renovar certificados Let's Encrypt", "params": {}},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.web_server = self.module_config.get("web_server", "auto")
        if self.web_server == "auto":
            self.web_server = detect_web_server()
        if not self.web_server:
            self.web_server = "nginx"  # default

    def render_summary(self) -> str:
        active = service_is_active(self.web_server)
        state = "activo" if active else "inactivo o no instalado"
        return f"Servidor web: {self.web_server} ({state})"

    def action_status(self) -> str:
        return service_status(self.web_server)

    def action_restart(self, service=None) -> str:
        svc = service or self.web_server
        return self.run_command(f"systemctl restart {svc}", use_sudo=True)[2] or "OK"

    def action_reload(self, service=None) -> str:
        svc = service or self.web_server
        return self.run_command(f"systemctl reload {svc}", use_sudo=True)[2] or "OK"

    def action_config_check(self, service=None) -> str:
        svc = service or self.web_server
        if svc in ["nginx", "apache2", "httpd"]:
            if svc == "nginx":
                return self.run_command("nginx -t")[2] or "Configuracion OK"
            elif svc in ["apache2", "httpd"]:
                return self.run_command("apachectl configtest")[2] or "Configuracion OK"
        return "Comando no soportado para este servidor"

    def action_logs_error(self, lines=50) -> str:
        if self.web_server == "nginx":
            path = "/var/log/nginx/error.log"
        elif self.web_server in ["apache2", "httpd"]:
            path = "/var/log/apache2/error.log"
        else:
            return "No se puede determinar ruta de logs"
        code, out, err = self.run_command(f"tail -n {lines} {path}")
        return out if code == 0 else f"Error: {err}"

    def action_logs_access(self, lines=50) -> str:
        if self.web_server == "nginx":
            path = "/var/log/nginx/access.log"
        elif self.web_server in ["apache2", "httpd"]:
            path = "/var/log/apache2/access.log"
        else:
            return "No se puede determinar ruta de logs"
        code, out, err = self.run_command(f"tail -n {lines} {path}")
        return out if code == 0 else f"Error: {err}"

    def action_cert_renew(self) -> str:
        return self.run_command("certbot renew --quiet", use_sudo=True)[2] or "Certificados renovados"


ModuleRegistry.register(Module)
