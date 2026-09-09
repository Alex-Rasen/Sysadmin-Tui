"""
Punto de entrada principal para sysadmin-tui.
Permite ejecutar la interfaz interactiva o comandos directos.
"""
import sys
import argparse
from src.app import SysAdminApp
from src.config import AppConfig
from src.executor import CommandExecutor
from src.logger import AuditLogger


def main():
    parser = argparse.ArgumentParser(
        prog="sysadmin-tui",
        description="Panel de administracion de servidores Linux"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Ruta al archivo de configuracion YAML"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Desactiva las confirmaciones para acciones destructivas (modo script)"
    )
    parser.add_argument(
        "module",
        nargs="?",
        default=None,
        help="Modulo a ejecutar en modo no interactivo (ej: containers)"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default=None,
        help="Accion a ejecutar en el modulo (ej: list)"
    )
    parser.add_argument(
        "params",
        nargs=argparse.REMAINDER,
        help="Parametros adicionales para la accion"
    )

    args = parser.parse_args()

    # Modo interactivo (por defecto)
    if args.module is None and args.action is None:
        app = SysAdminApp(config_path=args.config, confirm_destructive=not args.no_confirm)
        app.run()
        return 0

    # Modo no interactivo
    if args.module is None or args.action is None:
        parser.error("Para modo no interactivo se requieren modulo y accion.")
        return 1

    # Importar modulo y ejecutar accion
    try:
        mod = __import__(f"src.modules.{args.module}", fromlist=["Module"])
        module_class = getattr(mod, "Module")
        config = AppConfig.load(args.config)
        executor = CommandExecutor(config)
        logger = AuditLogger(config.audit_log)
        instance = module_class(config, executor, logger)
        result = instance.execute_action(args.action, args.params)
        if result:
            print(result)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
