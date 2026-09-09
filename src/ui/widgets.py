"""
Widgets reutilizables para la interfaz de usuario.
"""
from textual.widgets import Static


class InfoPanel(Static):
    """Panel simple para mostrar informacion."""

    def __init__(self, content: str = "", **kwargs):
        super().__init__(content, **kwargs)


class ActionList(Static):
    """Lista de acciones disponibles en un modulo."""

    def __init__(self, actions: list = None, **kwargs):
        content = "\n".join(f"* {a}" for a in (actions or []))
        super().__init__(content, **kwargs)
