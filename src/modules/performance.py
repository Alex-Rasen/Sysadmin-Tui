"""
Modulo de rendimiento y tuning.
"""
import os
from typing import Any, Dict, List

from src.modules.base import BaseModule, ModuleRegistry


class Module(BaseModule):
    display_name = "Rendimiento"
    name = "performance"
    actions = {
        "process_viewer": {"description": "Visor de tareas", "params": {}},
        "terminate_process": {"description": "Terminar proceso", "params": {"pid": "int"}},
        "sysctl_list": {"description": "Listar parametros sysctl", "params": {}},
        "sysctl_set": {"description": "Establecer parametro sysctl", "params": {"key": "str", "value": "str"}},
        "swap_info": {"description": "Informacion de swap", "params": {}},
        "top": {"description": "Monitor de procesos en tiempo real (top)", "params": {}},
    }

    def render_summary(self) -> str:
        return "Modulo de rendimiento"

    def list_processes(self, sort_by: str = "cpu", limit: int = 80) -> List[Dict[str, Any]]:
        """Devuelve procesos con metricas tipo htop usando ps y /proc."""
        sort_keys = {
            "cpu": "cpu_percent",
            "ram": "ram_bytes",
            "disk": "disk_bytes",
            "net": "net_connections",
        }
        sort_key = sort_keys.get(sort_by, "cpu_percent")
        rows = self._process_rows()
        network_by_pid = self._network_connections_by_pid()

        for row in rows:
            pid = row["pid"]
            io_stats = self._process_io(pid)
            row["read_bytes"] = io_stats["read_bytes"]
            row["write_bytes"] = io_stats["write_bytes"]
            row["disk_bytes"] = io_stats["read_bytes"] + io_stats["write_bytes"]
            row["net_connections"] = network_by_pid.get(pid, 0)

        rows.sort(key=lambda item: item.get(sort_key, 0), reverse=True)
        return rows[:limit]

    def action_process_viewer(self) -> str:
        lines = ["PID\tUSER\tCPU%\tRAM%\tRAM\tDISK\tNET\tCOMMAND"]
        for row in self.list_processes():
            lines.append(
                "\t".join(
                    [
                        str(row["pid"]),
                        row["user"],
                        f"{row['cpu_percent']:.1f}",
                        f"{row['ram_percent']:.1f}",
                        self.format_bytes(row["ram_bytes"]),
                        self.format_bytes(row["disk_bytes"]),
                        str(row["net_connections"]),
                        row["command"],
                    ]
                )
            )
        return "\n".join(lines)

    def action_terminate_process(self, pid) -> str:
        pid = int(pid)
        if pid <= 1:
            return "Error: no se permite terminar procesos criticos del sistema"
        if pid == os.getpid():
            return "Error: no se puede terminar el proceso de la aplicacion"
        code, out, err = self.run_command(f"kill -TERM {pid}")
        if code != 0:
            code, out, err = self.run_command(f"kill -TERM {pid}", use_sudo=True)
        if code == 0:
            return f"Proceso {pid} terminado"
        return f"Error: {err.strip() or out.strip() or 'no se pudo terminar el proceso'}"

    def _process_rows(self) -> List[Dict[str, Any]]:
        command = "ps -eo pid=,ppid=,user=,stat=,pcpu=,pmem=,rss=,comm=,args="
        code, out, err = self.run_command(command)
        if code != 0:
            return []
        rows: List[Dict[str, Any]] = []
        for line in out.splitlines():
            parts = line.strip().split(None, 8)
            if len(parts) < 8:
                continue
            args = parts[8] if len(parts) > 8 else parts[7]
            try:
                pid = int(parts[0])
                rss_kb = int(float(parts[6]))
                cpu_percent = float(parts[4].replace(",", "."))
                ram_percent = float(parts[5].replace(",", "."))
            except ValueError:
                continue
            rows.append(
                {
                    "pid": pid,
                    "ppid": parts[1],
                    "user": parts[2],
                    "state": parts[3],
                    "cpu_percent": cpu_percent,
                    "ram_percent": ram_percent,
                    "ram_bytes": rss_kb * 1024,
                    "name": parts[7],
                    "command": args[:120],
                }
            )
        return rows

    def _process_io(self, pid: int) -> Dict[str, int]:
        stats = {"read_bytes": 0, "write_bytes": 0}
        try:
            with open(f"/proc/{pid}/io", "r", encoding="utf-8") as io_file:
                for line in io_file:
                    key, _, value = line.partition(":")
                    if key in stats:
                        stats[key] = int(value.strip())
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            pass
        return stats

    def _network_connections_by_pid(self) -> Dict[int, int]:
        socket_inodes = self._network_socket_inodes()
        if not socket_inodes:
            return {}
        counts: Dict[int, int] = {}
        for entry in os.scandir("/proc"):
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            fd_dir = os.path.join(entry.path, "fd")
            try:
                for fd_entry in os.scandir(fd_dir):
                    try:
                        target = os.readlink(fd_entry.path)
                    except (FileNotFoundError, PermissionError, ProcessLookupError):
                        continue
                    if target.startswith("socket:[") and target[8:-1] in socket_inodes:
                        counts[pid] = counts.get(pid, 0) + 1
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
        return counts

    def _network_socket_inodes(self) -> set[str]:
        inodes: set[str] = set()
        for name in ("tcp", "tcp6", "udp", "udp6"):
            path = f"/proc/net/{name}"
            try:
                with open(path, "r", encoding="utf-8") as net_file:
                    next(net_file, None)
                    for line in net_file:
                        parts = line.split()
                        if len(parts) > 9:
                            inodes.add(parts[9])
            except (FileNotFoundError, PermissionError):
                continue
        return inodes

    def format_bytes(self, value: int) -> str:
        units = ("B", "K", "M", "G", "T")
        amount = float(value)
        for unit in units:
            if amount < 1024 or unit == units[-1]:
                return f"{amount:.1f}{unit}" if unit != "B" else f"{int(amount)}B"
            amount /= 1024
        return f"{value}B"

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
