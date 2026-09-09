"""
Modulo de almacenamiento y sistemas de archivos.
"""
from src.modules.base import BaseModule, ModuleRegistry
from src.utils.formatters import format_bytes


class Module(BaseModule):
    display_name = "Almacenamiento"
    name = "storage"
    actions = {
        "disks": {"description": "Listar discos y particiones", "params": {}},
        "usage": {"description": "Uso de espacio en sistemas de archivos", "params": {}},
        "mount": {"description": "Montar sistema de archivos", "params": {"device": "str", "mountpoint": "str"}},
        "umount": {"description": "Desmontar sistema de archivos", "params": {"mountpoint": "str"}},
        "lvm_info": {"description": "Informacion LVM", "params": {}},
    }

    def render_summary(self) -> str:
        return self.action_usage()

    def action_disks(self) -> str:
        return self.run_command("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT")[1]

    def action_usage(self) -> str:
        return self.run_command("df -h")[1]

    def action_mount(self, device, mountpoint) -> str:
        return self.run_command(f"mount {device} {mountpoint}", use_sudo=True)[2] or "Montado correctamente"

    def action_umount(self, mountpoint) -> str:
        return self.run_command(f"umount {mountpoint}", use_sudo=True)[2] or "Desmontado correctamente"

    def action_lvm_info(self) -> str:
        pvs = self.run_command("pvs")[1] or "Sin PVs"
        vgs = self.run_command("vgs")[1] or "Sin VGs"
        lvs = self.run_command("lvs")[1] or "Sin LVs"
        return f"PVs:\n{pvs}\n\nVGs:\n{vgs}\n\nLVs:\n{lvs}"


ModuleRegistry.register(Module)
