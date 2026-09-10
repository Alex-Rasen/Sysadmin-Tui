"""
Aplicacion principal Textual que integra todos los modulos.
Proporciona una interfaz interactiva completa:
- Lista de modulos
- Lista de acciones del modulo seleccionado
- Formulario dinamico para parametros de la accion
- Ejecucion y muestra de resultados
"""
import re
from typing import Optional, Dict, Any, List
from textual.timer import Timer
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label, Input, Button, DataTable
from textual.binding import Binding

# Importar modulo para registrar todos los modulos
import src.modules  # noqa: F401
from src.config import AppConfig
from src.logger import AuditLogger
from src.executor import CommandExecutor
from src.modules.base import ModuleRegistry, BaseModule
from src.utils.system import list_active_services


class SysAdminApp(App):
    """Aplicacion TUI principal."""

    TITLE = "SysAdmin TUI"
    SUB_TITLE = "Panel de administracion de servidores Linux"
    CSS = """
    #sidebar {
        width: 25%;
        max-width: 30;
        border-right: solid $primary;
        height: 100%;
    }
    #content {
        width: 75%;
        height: 100%;
        padding: 1;
    }
    #module_list {
        height: 100%;
    }
    #services_table {
        height: 14;
        margin-bottom: 1;
    }
    #container_images_table {
        height: 10;
        margin-bottom: 1;
    }
    #result_table {
        height: 1fr;
        margin-bottom: 1;
    }
    #process_table {
        height: 1fr;
        margin-bottom: 1;
    }
    #process_actions {
        height: auto;
        margin-bottom: 1;
    }
    .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }
    .action-grid {
        height: auto;
        margin-bottom: 1;
        width: 100%;
    }
    .action-grid Button {
        width: 100%;
        min-width: 0;
        padding: 0 1;
        margin: 0 0 1 0;
    }
    .status-panel {
        border: round $primary;
        padding: 1;
        margin-bottom: 1;
    }
    .sidebar-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }
    .content-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    .form-container {
        padding: 1;
    }
    .form-field {
        margin-bottom: 1;
    }
    Button {
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Salir"),
        Binding("f1", "show_help", "Ayuda"),
        Binding("escape", "go_back", "Atrás"),
        Binding("ctrl+s", "execute_action", "Ejecutar"),
    ]

    def __init__(self, config_path=None, confirm_destructive=True):
        super().__init__()
        self.config = AppConfig.load(config_path)
        self.confirm_destructive = confirm_destructive
        self.logger = AuditLogger(self.config.audit_log)
        self.executor = CommandExecutor(self.config)
        self.registry = ModuleRegistry()
        self.current_module: Optional[BaseModule] = None
        self.current_action: Optional[str] = None
        self.action_params: Dict[str, Any] = {}
        self.action_inputs: Dict[str, Input] = {}
        self.selected_service: Optional[str] = None
        self.selected_process_pid: Optional[int] = None
        self.process_sort_by: str = "cpu"
        self.performance_refresh_timer: Optional[Timer] = None
        self.state: str = "modules"  # "modules", "dashboard", "form", "result"

    SERVICE_KEYWORDS = {
        "containers": ["docker", "containerd", "podman", "crio"],
        "web_services": ["nginx", "apache", "httpd", "caddy", "php-fpm"],
        "firewall": ["ufw", "firewalld", "nftables", "iptables"],
        "network": ["network", "resolved", "dns", "ssh", "systemd-networkd"],
        "databases": ["postgres", "mysql", "mariadb", "mongo", "redis"],
        "api_microservices": ["api", "gunicorn", "uvicorn", "node", "pm2"],
        "storage": ["udisks", "lvm", "smart", "nfs", "smb", "mount"],
        "monitoring": ["prometheus", "grafana", "node-exporter", "telegraf", "zabbix"],
        "automation": ["cron", "atd", "timer"],
        "users": ["sssd", "nslcd", "ldap", "ssh"],
        "updates": ["apt", "dnf", "yum", "packagekit", "unattended"],
        "backups": ["backup", "borg", "restic", "rsync", "duplicity"],
        "performance": ["tuned", "irqbalance", "sysstat"],
        "virtualization": ["libvirtd", "virt", "qemu", "kvm"],
        "audit": ["auditd", "journald", "rsyslog", "syslog"],
    }

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("MODULOS", classes="sidebar-title")
                yield ListView(id="module_list")
            with Vertical(id="content"):
                yield ScrollableContainer(id="content_scroll")
        yield Footer()

    async def on_mount(self) -> None:
        self.query_one("#module_list", ListView).focus()
        self._populate_module_list()
        self.performance_refresh_timer = self.set_interval(2.0, self._refresh_process_table)
        await self._show_initial_module()

    def _populate_module_list(self) -> None:
        """Llena la lista de modulos en la barra lateral."""
        list_view = self.query_one("#module_list", ListView)
        list_view.clear()
        for mod_name, mod_class in self.registry.get_all().items():
            list_view.append(ListItem(Label(mod_class.display_name)))

    async def _show_initial_module(self) -> None:
        mod_names = list(self.registry.get_all().keys())
        if not mod_names:
            return
        index = mod_names.index("performance") if "performance" in mod_names else 0
        self.query_one("#module_list", ListView).index = index
        await self._show_module_by_index(index)

    async def _show_module_by_index(self, index: int) -> None:
        mod_names = list(self.registry.get_all().keys())
        if index >= len(mod_names):
            return
        mod_name = mod_names[index]
        mod_class = self.registry.get_all()[mod_name]
        self.current_module = mod_class(self.config, self.executor, self.logger)
        self.selected_service = None
        self.selected_process_pid = None
        self.state = "dashboard"
        await self._populate_module_dashboard()

    def _compact_button(self, label: str, *, id: str, variant: str = "default") -> Button:
        return Button(label, id=id, variant=variant, compact=True)

    async def _populate_module_dashboard(self) -> None:
        """Muestra una vista GUI con servicios activos y botones de accion."""
        content = self.query_one("#content_scroll", ScrollableContainer)
        await content.remove_children()
        if not self.current_module:
            return
        await content.mount(Static(f"Modulo: {self.current_module.display_name}", classes="content-title"))
        if self.current_module.name == "performance":
            await self._mount_performance_dashboard(content)
            return
        await content.mount(Static("Servicios activos", classes="section-title"))
        table = DataTable(id="services_table")
        table.cursor_type = "row"
        table.add_columns("Servicio", "Estado", "Detalle")
        services = self._services_for_current_module()
        if services:
            for service in services:
                table.add_row(
                    service["unit"],
                    service["sub"],
                    service["description"] or "-",
                    key=service["unit"],
                )
        else:
            table.add_row("Sin servicios activos detectados", "-", "No hay unidades systemd relevantes")
        await content.mount(table)

        if self.current_module.name == "containers":
            await self._mount_container_images(content)

        await content.mount(Static("Acciones", classes="section-title"))
        actions = Vertical(classes="action-grid")
        await content.mount(actions)
        for action_name, action_def in self.current_module.actions.items():
            desc = action_def.get("description", action_name)
            await actions.mount(self._compact_button(desc, id=f"action_{action_name}"))
        await content.mount(self._compact_button("Detalle del servicio seleccionado", id="btn_service_detail", variant="primary"))
        table.focus()

    async def _mount_performance_dashboard(self, content: ScrollableContainer) -> None:
        await content.mount(Static("Visor de tareas", classes="section-title"))
        actions = Vertical(id="process_actions", classes="action-grid")
        await content.mount(actions)
        await actions.mount(self._compact_button("CPU", id="sort_cpu", variant="primary" if self.process_sort_by == "cpu" else "default"))
        await actions.mount(self._compact_button("RAM", id="sort_ram", variant="primary" if self.process_sort_by == "ram" else "default"))
        await actions.mount(self._compact_button("Disco", id="sort_disk", variant="primary" if self.process_sort_by == "disk" else "default"))
        await actions.mount(self._compact_button("Red", id="sort_net", variant="primary" if self.process_sort_by == "net" else "default"))
        await actions.mount(self._compact_button("Actualizar", id="btn_process_refresh"))
        await actions.mount(self._compact_button("Terminar proceso", id="btn_process_kill", variant="error"))

        table = DataTable(id="process_table")
        table.cursor_type = "row"
        table.add_columns("PID", "USER", "S", "CPU%", "RAM%", "RAM", "DISCO", "RED", "COMANDO")
        await content.mount(table)
        await self._refresh_process_table()
        table.focus()

        await content.mount(Static("Acciones", classes="section-title"))
        module_actions = Vertical(classes="action-grid")
        await content.mount(module_actions)
        for action_name, action_def in self.current_module.actions.items():
            if action_name in {"process_viewer", "terminate_process"}:
                continue
            desc = action_def.get("description", action_name)
            await module_actions.mount(self._compact_button(desc, id=f"action_{action_name}"))

    async def _refresh_process_table(self) -> None:
        if self.state != "dashboard" or not self.current_module or self.current_module.name != "performance":
            return
        try:
            table = self.query_one("#process_table", DataTable)
        except Exception:
            return
        table.clear(columns=False)
        processes = self.current_module.list_processes(self.process_sort_by)
        if not processes:
            table.add_row("-", "-", "-", "-", "-", "-", "-", "-", "No se pudieron leer procesos")
            return
        for process in processes:
            table.add_row(
                str(process["pid"]),
                process["user"],
                process["state"],
                f"{process['cpu_percent']:.1f}",
                f"{process['ram_percent']:.1f}",
                self.current_module.format_bytes(process["ram_bytes"]),
                self.current_module.format_bytes(process["disk_bytes"]),
                str(process["net_connections"]),
                process["command"],
                key=str(process["pid"]),
            )

    async def _mount_container_images(self, content: ScrollableContainer) -> None:
        """Muestra las imagenes disponibles del runtime de contenedores."""
        if not self.current_module:
            return
        await content.mount(Static("Imagenes disponibles", classes="section-title"))
        result = self.current_module.execute_action("images", {})
        rows = self._result_rows(result or "")
        image_table = DataTable(id="container_images_table")
        image_table.cursor_type = "row"
        if not rows:
            rows = [{"Repositorio": "-", "Etiqueta": "-", "ID": "-", "Tamano": self._friendly_result_message(result or "Sin imagenes disponibles", True)}]
        columns = self._normalize_columns(rows)
        image_table.add_columns(*columns)
        for row in rows:
            image_table.add_row(*(row.get(column, "") for column in columns))
        await content.mount(image_table)

    def _services_for_current_module(self) -> List[Dict[str, str]]:
        if not self.current_module:
            return []
        services = list_active_services()
        keywords = self.SERVICE_KEYWORDS.get(self.current_module.name, [])
        if not keywords:
            return services[:25]
        filtered = [
            service for service in services
            if any(keyword in f"{service['unit']} {service['description']}".lower() for keyword in keywords)
        ]
        return filtered[:25]

    async def _show_form(self, action_name: str) -> None:
        """Muestra un formulario para los parametros de la accion."""
        self.current_action = action_name
        action_def = self.current_module.actions[action_name]
        params_spec = action_def.get("params", {})
        content = self.query_one("#content_scroll", ScrollableContainer)
        await content.remove_children()
        desc = action_def.get("description", action_name)
        await content.mount(Static(f"Acción: {desc}", classes="content-title"))
        form_container = Vertical(classes="form-container")
        await content.mount(form_container)
        self.action_inputs = {}
        for param_name, param_type in params_spec.items():
            is_optional = param_type.endswith("?")
            type_str = param_type.rstrip("?") if is_optional else param_type
            label = f"{param_name} ({type_str})" + (" [opcional]" if is_optional else "")
            await form_container.mount(Label(label))
            input_widget = Input(placeholder=label, id=f"input_{param_name}")
            await form_container.mount(input_widget)
            self.action_inputs[param_name] = input_widget
        execute_btn = Button("Ejecutar", variant="primary", id="btn_execute")
        await form_container.mount(execute_btn)

    async def _execute_current_action(self) -> None:
        """Recopila parametros del formulario y ejecuta la accion."""
        if not self.current_module or not self.current_action:
            return
        params = {}
        for param_name, input_widget in self.action_inputs.items():
            value = input_widget.value.strip()
            if value:
                param_type = self.current_module.actions[self.current_action]["params"].get(param_name, "str")
                type_str = param_type.rstrip("?")
                if type_str == "int":
                    try:
                        params[param_name] = int(value)
                    except ValueError:
                        self.notify(f"El parametro {param_name} debe ser entero", severity="error")
                        return
                else:
                    params[param_name] = value
        try:
            result = self.current_module.execute_action(self.current_action, params)
            await self._show_result(result, success=True)
        except Exception as e:
            await self._show_result(str(e), success=False)

    async def _show_result(self, result: str, success: bool = True) -> None:
        """Muestra el resultado de una accion en controles GUI."""
        self.state = "result"
        content = self.query_one("#content_scroll", ScrollableContainer)
        await content.remove_children()
        title = "Acción completada" if success else "Acción con errores"
        await content.mount(Static(title, classes="content-title"))
        result = result or "Sin datos adicionales"
        rows = self._result_rows(result)
        if rows:
            table = DataTable(id="result_table")
            table.cursor_type = "row"
            columns = self._normalize_columns(rows)
            table.add_columns(*columns)
            for row in rows:
                table.add_row(*(row.get(column, "") for column in columns))
            await content.mount(table)
        else:
            message = self._friendly_result_message(result, success)
            await content.mount(Static(message, classes="status-panel"))
        back_btn = Button("Volver", id="btn_back")
        await content.mount(back_btn)

    def _normalize_columns(self, rows: List[Dict[str, str]]) -> List[str]:
        columns: List[str] = []
        for row in rows:
            for column in row.keys():
                if column not in columns:
                    columns.append(column)
        return columns[:8] or ["Resultado"]

    def _result_rows(self, text: str) -> List[Dict[str, str]]:
        clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not clean_lines:
            return []
        systemctl_rows = self._systemctl_status_rows(clean_lines)
        if systemctl_rows:
            return systemctl_rows
        if clean_lines[0].lower().startswith(("error:", "traceback")):
            return []
        if len(clean_lines) == 1 and not self._looks_tabular(clean_lines[0]):
            return []

        rows: List[Dict[str, str]] = []
        if all(":" in line and not line.lower().startswith(("error:", "traceback")) for line in clean_lines):
            for line in clean_lines:
                key, value = line.split(":", 1)
                rows.append({"Campo": key.strip(), "Valor": value.strip() or "-"})
            return rows

        header = self._split_columns(clean_lines[0])
        has_header = len(header) > 1 and any(not part.isdigit() for part in header)
        data_lines = clean_lines[1:] if has_header else clean_lines
        columns = header if has_header else ["Linea", "Detalle"]
        for index, line in enumerate(data_lines, start=1):
            parts = self._split_columns(line)
            if len(columns) == 2 and columns == ["Linea", "Detalle"]:
                rows.append({"Linea": str(index), "Detalle": line[:180]})
                continue
            row = {column: parts[pos] if pos < len(parts) else "" for pos, column in enumerate(columns)}
            if row:
                rows.append(row)
        return rows[:200]

    def _systemctl_status_rows(self, lines: List[str]) -> List[Dict[str, str]]:
        if not any(
            label in line.lower()
            for line in lines
            for label in ("loaded:", "active:", "main pid:")
        ):
            return []
        rows = []
        for label in ("Loaded", "Active", "Main PID"):
            prefix = f"{label}:"
            match = next((line for line in lines if line.lower().startswith(prefix.lower())), None)
            if match:
                rows.append({"Campo": label, "Valor": match.split(":", 1)[1].strip()})
        return rows

    def _split_columns(self, line: str) -> List[str]:
        if "\t" in line:
            return [part.strip() for part in line.split("\t") if part.strip()]
        return [part.strip() for part in re.split(r"\s{2,}", line) if part.strip()]

    def _looks_tabular(self, line: str) -> bool:
        return "\t" in line or bool(re.search(r"\s{2,}", line)) or ":" in line

    def _friendly_result_message(self, result: str, success: bool) -> str:
        lowered = result.lower()
        if lowered.startswith(("error:", "traceback")):
            return "La operación no pudo completarse. Revisa permisos, parámetros o disponibilidad del servicio."
        if success and lowered in {"ok", "success"}:
            return "La operación finalizó correctamente."
        if success and len(result) < 120 and not any(token in lowered for token in ["●", "loaded:", "active:", "journal", "systemctl"]):
            return result
        if not success:
            return "La operación no pudo completarse. Revisa permisos, parámetros o disponibilidad del servicio."
        return "La operación finalizó. El resultado fue resumido para mantener la vista en formato GUI."

    async def _go_back(self) -> None:
        """Navega hacia atrás segun el estado actual."""
        if self.state == "dashboard":
            self.state = "modules"
            self.query_one("#module_list", ListView).focus()
        elif self.state == "form":
            self.state = "dashboard"
            await self._populate_module_dashboard()
        elif self.state == "result":
            self.state = "dashboard"
            await self._populate_module_dashboard()
        # En state == "modules" no hacer nada

    async def action_go_back(self) -> None:
        await self._go_back()

    def action_show_help(self) -> None:
        self.notify("Ayuda no implementada aun", severity="information")

    async def action_execute_action(self) -> None:
        if self.state == "form":
            await self._execute_current_action()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "module_list":
            if not event.item:
                return
            index = event.list_view.index
            if index is None:
                return
            mod_names = list(self.registry.get_all().keys())
            await self._show_module_by_index(index)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_execute":
            await self._execute_current_action()
        elif event.button.id == "btn_back":
            await self._go_back()
        elif event.button.id == "btn_service_detail":
            await self._show_selected_service_detail()
        elif event.button.id == "btn_process_refresh":
            await self._refresh_process_table()
        elif event.button.id == "btn_process_kill":
            await self._terminate_selected_process()
        elif event.button.id and event.button.id.startswith("sort_"):
            self.process_sort_by = event.button.id.replace("sort_", "", 1)
            await self._populate_module_dashboard()
        elif event.button.id and event.button.id.startswith("action_"):
            action_name = event.button.id.replace("action_", "", 1)
            if self.current_module and action_name in self.current_module.actions:
                params_spec = self.current_module.actions[action_name].get("params", {})
                self.current_action = action_name
                if params_spec:
                    self.state = "form"
                    await self._show_form(action_name)
                else:
                    self.action_inputs = {}
                    await self._execute_current_action()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "services_table" and event.row_key is not None:
            value = event.row_key.value
            if value != "Sin servicios activos detectados":
                self.selected_service = str(value)
        elif event.data_table.id == "process_table" and event.row_key is not None:
            value = event.row_key.value
            if str(value).isdigit():
                self.selected_process_pid = int(str(value))

    async def _terminate_selected_process(self) -> None:
        if not self.current_module or self.current_module.name != "performance":
            return
        try:
            table = self.query_one("#process_table", DataTable)
            if table.cursor_row is not None and table.cursor_row < len(table.rows):
                key = list(table.rows.keys())[table.cursor_row]
                value = str(key.value)
                if value.isdigit():
                    self.selected_process_pid = int(value)
        except Exception:
            pass
        if not self.selected_process_pid:
            self.notify("Selecciona un proceso en la tabla", severity="warning")
            return
        result = self.current_module.execute_action("terminate_process", {"pid": self.selected_process_pid})
        if result and result.lower().startswith("error:"):
            self.notify(result, severity="error")
        else:
            self.notify(result or "Proceso terminado", severity="information")
        self.selected_process_pid = None
        await self._refresh_process_table()

    async def _show_selected_service_detail(self) -> None:
        self.state = "result"
        table = self.query_one("#services_table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(table.rows):
            key = list(table.rows.keys())[table.cursor_row]
            self.selected_service = str(key.value)
        if not self.selected_service or self.selected_service == "Sin servicios activos detectados":
            self.notify("Selecciona un servicio activo en la tabla", severity="warning")
            return
        content = self.query_one("#content_scroll", ScrollableContainer)
        await content.remove_children()
        await content.mount(Static(f"Servicio: {self.selected_service}", classes="content-title"))
        matching = [service for service in list_active_services() if service["unit"] == self.selected_service]
        table = DataTable(id="result_table")
        table.add_columns("Campo", "Valor")
        if matching:
            service = matching[0]
            labels = {
                "unit": "Servicio",
                "load": "Carga",
                "active": "Estado",
                "sub": "Subestado",
                "description": "Descripción",
            }
            for key, label in labels.items():
                table.add_row(label, service.get(key, "-") or "-")
        else:
            table.add_row("Estado", "No activo o no disponible")
        await content.mount(table)
        await content.mount(Button("Volver", id="btn_back"))
