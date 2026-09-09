"""
Modulo de gestion de bases de datos.
"""
from src.modules.base import BaseModule, ModuleRegistry
from src.utils.system import service_is_active


class Module(BaseModule):
    display_name = "Bases de Datos"
    name = "databases"
    actions = {
        "status": {"description": "Estado de servicios de BD", "params": {}},
        "list_databases": {"description": "Listar bases de datos", "params": {"engine": "str?"}},
        "backup": {"description": "Backup de una BD", "params": {"engine": "str", "db": "str", "output": "str?"}},
        "restore": {"description": "Restaurar BD desde backup", "params": {"engine": "str", "db": "str", "file": "str"}},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engines = ["postgres", "mysql", "mariadb", "mongodb", "redis"]
        self.active_engines = self._detect_active()

    def _detect_active(self):
        active = []
        for eng in self.engines:
            if service_is_active(eng) or service_is_active(eng + "d"):
                active.append(eng)
        return active

    def render_summary(self) -> str:
        if not self.active_engines:
            return "No hay servicios de bases de datos activos detectados."
        return "Bases de datos activas: " + ", ".join(self.active_engines)

    def action_status(self) -> str:
        lines = []
        for eng in self.engines:
            svc = eng if eng != "mariadb" else "mariadb"
            if service_is_active(svc):
                lines.append(f"{eng}: activo")
            else:
                lines.append(f"{eng}: inactivo")
        return "\n".join(lines)

    def action_list_databases(self, engine=None) -> str:
        eng = engine or (self.active_engines[0] if self.active_engines else None)
        if not eng:
            return "No hay motor de BD especificado"
        if eng in ["postgres", "postgresql"]:
            return self.run_command("sudo -u postgres psql -l")[1]
        elif eng in ["mysql", "mariadb"]:
            return self.run_command("mysql -e 'SHOW DATABASES;'")[1]
        else:
            return f"Motor {eng} no soportado para listado"

    def action_backup(self, engine, db, output=None) -> str:
        out_file = output or f"/tmp/{db}_{engine}_backup.sql"
        if engine in ["postgres", "postgresql"]:
            cmd = f"sudo -u postgres pg_dump {db} > {out_file}"
        elif engine in ["mysql", "mariadb"]:
            cmd = f"mysqldump {db} > {out_file}"
        elif engine == "mongodb":
            cmd = f"mongodump --db {db} --out {out_file}"
        else:
            return "Motor no soportado para backup"
        code, out, err = self.run_command(cmd, use_sudo=True)
        if code == 0:
            return f"Backup realizado en {out_file}"
        return f"Error: {err}"

    def action_restore(self, engine, db, file) -> str:
        if engine in ["postgres", "postgresql"]:
            cmd = f"sudo -u postgres psql {db} < {file}"
        elif engine in ["mysql", "mariadb"]:
            cmd = f"mysql {db} < {file}"
        elif engine == "mongodb":
            cmd = f"mongorestore --db {db} {file}"
        else:
            return "Motor no soportado"
        code, out, err = self.run_command(cmd, use_sudo=True)
        if code == 0:
            return "Restauracion completada"
        return f"Error: {err}"


ModuleRegistry.register(Module)
