"""
Modulo de copias de seguridad y recuperacion.
"""
import os
from datetime import datetime
from src.modules.base import BaseModule, ModuleRegistry


class Module(BaseModule):
    display_name = "Copias de Seguridad"
    name = "backups"
    actions = {
        "backup_configs": {"description": "Backup de configuraciones importantes", "params": {}},
        "backup_db": {"description": "Backup de base de datos", "params": {"engine": "str", "db": "str"}},
        "list_backups": {"description": "Listar backups disponibles", "params": {}},
        "restore_backup": {"description": "Restaurar backup", "params": {"file": "str"}},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backup_dir = self.module_config.get("backup_dir", "/var/backups/sysadmin-tui")
        os.makedirs(self.backup_dir, exist_ok=True)

    def render_summary(self) -> str:
        return f"Directorio de backups: {self.backup_dir}"

    def action_backup_configs(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        tar_file = os.path.join(self.backup_dir, f"configs_{timestamp}.tar.gz")
        code, out, err = self.run_command(
            f"tar czf {tar_file} /etc/nginx /etc/apache2 /etc/ssh /etc/mysql /etc/postgresql /etc/sysctl.conf",
            use_sudo=True
        )
        if code == 0:
            return f"Backup de configuraciones creado en {tar_file}"
        return f"Error: {err}"

    def action_backup_db(self, engine, db) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        out_file = os.path.join(self.backup_dir, f"{db}_{engine}_{timestamp}.sql")
        if engine in ["postgres", "postgresql"]:
            cmd = f"sudo -u postgres pg_dump {db} > {out_file}"
        elif engine in ["mysql", "mariadb"]:
            cmd = f"mysqldump {db} > {out_file}"
        elif engine == "mongodb":
            cmd = f"mongodump --db {db} --out {out_file}"
        else:
            return "Motor no soportado"
        code, out, err = self.run_command(cmd, use_sudo=True)
        if code == 0:
            return f"Backup de BD en {out_file}"
        return f"Error: {err}"

    def action_list_backups(self) -> str:
        return self.run_command(f"ls -lh {self.backup_dir}")[1] or "No hay backups"

    def action_restore_backup(self, file) -> str:
        if not os.path.exists(file):
            return "Archivo no existe"
        # Implementar segun tipo
        if file.endswith(".sql"):
            return "Restauracion SQL no implementada en CLI; use el modulo de bases de datos"
        else:
            return self.run_command(f"tar xzf {file} -C /", use_sudo=True)[2] or "Restaurado"


ModuleRegistry.register(Module)
