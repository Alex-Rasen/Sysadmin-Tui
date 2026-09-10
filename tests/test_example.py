def test_import_modules():
    import src.modules
    from src.modules.base import ModuleRegistry
    modules = ModuleRegistry.get_all()
    assert len(modules) >= 15
    assert next(iter(modules)) == "performance"

def test_config_load():
    from src.config import AppConfig
    config = AppConfig.load(None)
    assert config.theme == "dark"

def test_performance_process_rows_shape():
    from src.config import AppConfig
    from src.executor import CommandExecutor
    from src.logger import AuditLogger
    from src.modules.performance import Module

    config = AppConfig.load(None)
    module = Module(config, CommandExecutor(config), AuditLogger(config.audit_log))
    processes = module.list_processes(limit=5)

    assert processes
    assert {"pid", "cpu_percent", "ram_bytes", "disk_bytes", "net_connections", "command"} <= set(processes[0])
