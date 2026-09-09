"""
Clase base para todos los modulos funcionales y registro de modulos.
"""
import abc
from typing import Dict, Type, List, Optional, Any, Tuple
from src.config import AppConfig
from src.executor import CommandExecutor
from src.logger import AuditLogger


class BaseModule(abc.ABC):
    """Define la interfaz comun para todos los modulos."""

    # Nombre para mostrar en el menu
    display_name: str = "Modulo Base"
    # Nombre interno (usado para CLI y configuracion)
    name: str = "base"
    # Lista de acciones disponibles (cada una con parametros)
    actions: Dict[str, Dict[str, Any]] = {}

    def __init__(self, config: AppConfig, executor: CommandExecutor, logger: AuditLogger):
        self.config = config
        self.executor = executor
        self.logger = logger
        self.module_config = config.get_module_config(self.name)

    @abc.abstractmethod
    def render_summary(self) -> str:
        """Devuelve un resumen textual del estado del modulo."""
        pass

    def execute_action(self, action_name: str, params: List[str] = None) -> Optional[str]:
        """Ejecuta una accion del modulo. Devuelve resultado como string."""
        if action_name not in self.actions:
            raise ValueError(f"Accion '{action_name}' no existe en modulo {self.name}")
        action = self.actions[action_name]
        handler_name = action.get("handler", action_name)
        handler = getattr(self, f"action_{handler_name}", None)
        if handler is None:
            raise NotImplementedError(f"Handler para accion '{action_name}' no implementado")
        # Convertir parametros de lista a diccionario simple
        kwargs = self._parse_params(params, action.get("params", {}))
        # Registrar auditoria
        start = __import__("time").time()
        try:
            result = handler(**kwargs)
            duration_ms = int((__import__("time").time() - start) * 1000)
            self.logger.log("execute", self.name, action_name, kwargs, "success", duration_ms)
            return result
        except Exception as e:
            duration_ms = int((__import__("time").time() - start) * 1000)
            self.logger.log("execute", self.name, action_name, kwargs, f"error: {e}", duration_ms)
            raise

    def _parse_params(self, params: List[str], param_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte lista de parametros en diccionario segun especificacion."""
        if isinstance(params, dict):
            return params
        result = {}
        if not params:
            return result
        # Soporte simple: --clave valor o posicional
        i = 0
        while i < len(params):
            arg = params[i]
            if arg.startswith("--"):
                key = arg[2:]
                if i + 1 < len(params) and not params[i + 1].startswith("--"):
                    result[key] = params[i + 1]
                    i += 2
                else:
                    result[key] = True
                    i += 1
            else:
                # Intentar asignar a la clave segun orden de param_spec
                keys = list(param_spec.keys())
                pos = len(result)
                if pos < len(keys):
                    result[keys[pos]] = arg
                i += 1
        return result

    def run_command(self, command: str, use_sudo: bool = False) -> Tuple[int, str, str]:
        """Conveniencia para ejecutar comandos."""
        return self.executor.run(command, use_sudo)


class ModuleRegistry:
    """Registro de todos los modulos disponibles."""

    _modules: Dict[str, Type[BaseModule]] = {}

    @classmethod
    def register(cls, module_class: Type[BaseModule]) -> None:
        cls._modules[module_class.name] = module_class

    @classmethod
    def get_all(cls) -> Dict[str, Type[BaseModule]]:
        return cls._modules

    @classmethod
    def get_all_names(cls) -> List[str]:
        return list(cls._modules.keys())

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseModule]]:
        return cls._modules.get(name)
