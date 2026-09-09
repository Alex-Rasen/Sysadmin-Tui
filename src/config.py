"""
Carga y validacion de la configuracion desde archivo YAML.
"""
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator
import yaml


class AppConfigModel(BaseModel):
    """Modelo de configuracion general."""
    theme: str = "dark"
    language: str = "es"
    confirm_destructive: bool = True
    log_level: str = "info"
    audit_log: str = "/var/log/sysadmin-tui/audit.jsonl"

    modules: Dict[str, Any] = {}
    sudo: Dict[str, Any] = {
        "use_sudo": True,
        "sudo_user": "root",
        "ask_password": True,
        "sudo_command": "/usr/bin/sudo",
    }

    @field_validator("audit_log")
    @classmethod
    def validate_audit_log(cls, v):
        if not v.startswith("/"):
            raise ValueError("audit_log debe ser una ruta absoluta")
        return v


class AppConfig:
    """Clase contenedora de configuracion cargada."""

    def __init__(self, data: AppConfigModel):
        self.data = data
        self.theme = data.theme
        self.language = data.language
        self.confirm_destructive = data.confirm_destructive
        self.log_level = data.log_level
        self.audit_log = data.audit_log
        self.modules = data.modules
        self.sudo = data.sudo

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AppConfig":
        """Carga configuracion desde archivo YAML o usa valores por defecto."""
        if config_path is None:
            # Buscar en ubicaciones estandar
            candidates = [
                os.path.join(os.getcwd(), "config.yaml"),
                os.path.expanduser("~/.config/sysadmin-tui/config.yaml"),
                "/etc/sysadmin-tui/config.yaml",
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    config_path = candidate
                    break

        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        else:
            raw = {}

        model = AppConfigModel(**raw)
        return cls(model)

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Devuelve la configuracion especifica de un modulo."""
        return self.modules.get(module_name, {})

    def is_module_enabled(self, module_name: str) -> bool:
        cfg = self.get_module_config(module_name)
        return cfg.get("enabled", True)
