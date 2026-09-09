"""
Modulo de gestion del firewall (UFW, firewalld, iptables/nftables).
"""
from src.modules.base import BaseModule, ModuleRegistry
from src.utils.system import detect_distro


class Module(BaseModule):
    display_name = "Firewall"
    name = "firewall"
    actions = {
        "status": {"description": "Estado del firewall", "params": {}},
        "enable": {"description": "Activar firewall", "params": {}},
        "disable": {"description": "Desactivar firewall", "params": {}},
        "allow_port": {"description": "Permitir puerto", "params": {"port": "int", "proto": "str?"}},
        "deny_port": {"description": "Denegar puerto", "params": {"port": "int", "proto": "str?"}},
        "allow_ip": {"description": "Permitir IP", "params": {"ip": "str"}},
        "deny_ip": {"description": "Denegar IP", "params": {"ip": "str"}},
        "list_rules": {"description": "Listar reglas", "params": {}},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.module_config.get("backend", "auto")
        if self.backend == "auto":
            distro = detect_distro()
            if distro in ["ubuntu", "debian", "linuxmint", "pop"]:
                self.backend = "ufw"
            elif distro in ["centos", "rhel", "fedora", "rocky", "almalinux"]:
                self.backend = "firewalld"
            else:
                self.backend = "iptables"
        self.backend = self.backend.lower()

    def render_summary(self) -> str:
        if self.backend == "ufw":
            out = self.run_command("ufw status")[1]
            return out if out else "UFW no esta activo"
        elif self.backend == "firewalld":
            out = self.run_command("firewall-cmd --state")[1]
            return f"Firewalld: {out.strip() if out else 'inactivo'}"
        else:
            out = self.run_command("iptables -L -n --line-numbers")[1]
            return "iptables activo" if out else "iptables sin reglas"

    def action_status(self) -> str:
        if self.backend == "ufw":
            return self.run_command("ufw status verbose")[1]
        elif self.backend == "firewalld":
            return self.run_command("firewall-cmd --list-all")[1]
        else:
            return self.run_command("iptables -L -n -v")[1]

    def action_enable(self) -> str:
        if self.backend == "ufw":
            return self.run_command("ufw enable", use_sudo=True)[2] or "UFW activado"
        elif self.backend == "firewalld":
            return self.run_command("systemctl start firewalld && systemctl enable firewalld", use_sudo=True)[2] or "Firewalld activado"
        return "No soportado"

    def action_disable(self) -> str:
        if self.backend == "ufw":
            return self.run_command("ufw disable", use_sudo=True)[2] or "UFW desactivado"
        elif self.backend == "firewalld":
            return self.run_command("systemctl stop firewalld && systemctl disable firewalld", use_sudo=True)[2] or "Firewalld desactivado"
        return "No soportado"

    def action_allow_port(self, port, proto="tcp") -> str:
        if self.backend == "ufw":
            return self.run_command(f"ufw allow {port}/{proto}", use_sudo=True)[2] or f"Puerto {port}/{proto} permitido"
        elif self.backend == "firewalld":
            return self.run_command(f"firewall-cmd --permanent --add-port={port}/{proto} && firewall-cmd --reload", use_sudo=True)[2] or "Regla agregada"
        else:
            return self.run_command(f"iptables -A INPUT -p {proto} --dport {port} -j ACCEPT", use_sudo=True)[2] or "Regla agregada"

    def action_deny_port(self, port, proto="tcp") -> str:
        if self.backend == "ufw":
            return self.run_command(f"ufw deny {port}/{proto}", use_sudo=True)[2] or f"Puerto {port}/{proto} denegado"
        elif self.backend == "firewalld":
            return self.run_command(f"firewall-cmd --permanent --remove-port={port}/{proto} && firewall-cmd --reload", use_sudo=True)[2] or "Regla eliminada"
        else:
            return self.run_command(f"iptables -A INPUT -p {proto} --dport {port} -j DROP", use_sudo=True)[2] or "Regla agregada"

    def action_allow_ip(self, ip) -> str:
        if self.backend == "ufw":
            return self.run_command(f"ufw allow from {ip}", use_sudo=True)[2] or f"IP {ip} permitida"
        elif self.backend == "firewalld":
            return self.run_command(f"firewall-cmd --permanent --add-source={ip} && firewall-cmd --reload", use_sudo=True)[2] or "Regla agregada"
        else:
            return self.run_command(f"iptables -A INPUT -s {ip} -j ACCEPT", use_sudo=True)[2] or "Regla agregada"

    def action_deny_ip(self, ip) -> str:
        if self.backend == "ufw":
            return self.run_command(f"ufw deny from {ip}", use_sudo=True)[2] or f"IP {ip} denegada"
        elif self.backend == "firewalld":
            return self.run_command(f"firewall-cmd --permanent --remove-source={ip} && firewall-cmd --reload", use_sudo=True)[2] or "Regla eliminada"
        else:
            return self.run_command(f"iptables -A INPUT -s {ip} -j DROP", use_sudo=True)[2] or "Regla agregada"

    def action_list_rules(self) -> str:
        if self.backend == "ufw":
            return self.run_command("ufw status numbered")[1]
        elif self.backend == "firewalld":
            return self.run_command("firewall-cmd --list-all")[1]
        else:
            return self.run_command("iptables -L -n --line-numbers")[1]


ModuleRegistry.register(Module)
