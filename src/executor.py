"""
Ejecutor seguro de comandos del sistema con soporte para sudo.
"""
import subprocess
import shlex
from typing import Optional, Tuple
from src.config import AppConfig


class CommandExecutor:
    """Envuelve subprocess para ejecutar comandos de forma controlada."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.sudo_cfg = config.sudo
        self.use_sudo = self.sudo_cfg.get("use_sudo", True)
        self.sudo_command = self.sudo_cfg.get("sudo_command", "/usr/bin/sudo")
        self.ask_password = self.sudo_cfg.get("ask_password", False)

    def _needs_shell(self, command: str) -> bool:
        """Detecta comandos que requieren evaluacion de shell."""
        shell_tokens = ("|", "&&", "||", ">", "<", ";", "$(", "`", "*")
        return any(token in command for token in shell_tokens)

    def _build_args(self, command: str, use_sudo: bool) -> list[str]:
        sudo_args = []
        if use_sudo and self.use_sudo:
            sudo_args = shlex.split(self.sudo_command)
            sudo_args.append("-S" if self.ask_password else "-n")

        if self._needs_shell(command):
            return sudo_args + ["bash", "-lc", command]
        return sudo_args + shlex.split(command)

    def run(self, command: str, use_sudo: bool = False, check: bool = False,
            input_text: Optional[str] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """
        Ejecuta un comando y devuelve (returncode, stdout, stderr).
        Si use_sudo=True, antepone sudo al comando.
        """
        args = self._build_args(command, use_sudo)
        try:
            proc = subprocess.run(
                args,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return 124, "", "Timeout expirado"
        except FileNotFoundError as e:
            return 127, "", str(e)

    def run_quiet(self, command: str, use_sudo: bool = False, check: bool = False,
                  timeout: Optional[int] = None) -> Optional[str]:
        """Ejecuta un comando y devuelve stdout si success, None en caso de error."""
        code, out, err = self.run(command, use_sudo, check, timeout=timeout)
        if code == 0:
            return out.strip()
        return None
