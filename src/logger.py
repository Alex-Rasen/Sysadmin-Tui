"""
Sistema de registro de auditoria en formato JSONL.
"""
import json
import os
import time
from datetime import datetime
from typing import Any, Dict


class AuditLogger:
    """Registra acciones ejecutadas en un archivo JSONL."""

    def __init__(self, log_path: str):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log(self, event: str, module: str, action: str, params: Dict[str, Any] = None,
            result: str = "success", duration_ms: int = 0, user: str = None) -> None:
        """Escribe un registro de auditoria."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": user or os.getenv("USER", "unknown"),
            "event": event,
            "module": module,
            "action": action,
            "params": params or {},
            "result": result,
            "duration_ms": duration_ms,
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # No interrumpir la ejecucion por fallo de logging
