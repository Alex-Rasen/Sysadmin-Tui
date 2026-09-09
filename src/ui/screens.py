"""
Pantallas adicionales para la interfaz (formularios, resultados).
"""
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Grid


class ConfirmScreen(Screen):
    """Pantalla de confirmacion para acciones destructivas."""

    def __init__(self, message: str, on_confirm, on_cancel):
        super().__init__()
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

    def compose(self):
        yield Static(self.message, id="confirm_message")
        with Grid(id="confirm_buttons"):
            yield Button("Si", variant="error", id="btn_yes")
            yield Button("No", variant="primary", id="btn_no")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_yes":
            self.on_confirm()
            self.dismiss(True)
        else:
            self.on_cancel()
            self.dismiss(False)
