def test_import_modules():
    import src.modules
    from src.modules.base import ModuleRegistry
    modules = ModuleRegistry.get_all()
    assert len(modules) >= 15

def test_config_load():
    from src.config import AppConfig
    config = AppConfig.load(None)
    assert config.theme == "dark"
