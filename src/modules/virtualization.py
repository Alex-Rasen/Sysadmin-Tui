"""
Modulo de virtualizacion (KVM/QEMU).
"""
from src.modules.base import BaseModule, ModuleRegistry


class Module(BaseModule):
    display_name = "Virtualizacion"
    name = "virtualization"
    actions = {
        "list_vms": {"description": "Listar maquinas virtuales", "params": {}},
        "start_vm": {"description": "Iniciar VM", "params": {"name": "str"}},
        "stop_vm": {"description": "Detener VM", "params": {"name": "str"}},
        "info_vm": {"description": "Informacion de VM", "params": {"name": "str"}},
    }

    def render_summary(self) -> str:
        vms = self.run_command("virsh list --all")[1]
        return vms if vms else "No se pudo obtener lista de VMs"

    def action_list_vms(self) -> str:
        return self.run_command("virsh list --all")[1]

    def action_start_vm(self, name) -> str:
        return self.run_command(f"virsh start {name}", use_sudo=True)[2] or f"VM {name} iniciada"

    def action_stop_vm(self, name) -> str:
        return self.run_command(f"virsh shutdown {name}", use_sudo=True)[2] or f"VM {name} apagada"

    def action_info_vm(self, name) -> str:
        return self.run_command(f"virsh dominfo {name}")[1] or "No se pudo obtener info"


ModuleRegistry.register(Module)
