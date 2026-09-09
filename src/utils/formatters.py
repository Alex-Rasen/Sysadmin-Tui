"""
Funciones de formato para salida de datos.
"""


def format_bytes(num_bytes: int) -> str:
    """Convierte bytes a formato legible."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024**2:
        return f"{num_bytes/1024:.1f} KiB"
    elif num_bytes < 1024**3:
        return f"{num_bytes/1024**2:.1f} MiB"
    elif num_bytes < 1024**4:
        return f"{num_bytes/1024**3:.1f} GiB"
    else:
        return f"{num_bytes/1024**4:.1f} TiB"


def format_table(headers: list, rows: list) -> str:
    """Formatea datos como tabla ASCII simple."""
    if not rows:
        return "Sin datos"
    col_widths = []
    for i, h in enumerate(headers):
        max_len = len(str(h))
        for row in rows:
            if i < len(row):
                max_len = max(max_len, len(str(row[i])))
        col_widths.append(max_len)
    header = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    sep = "-+-".join("-" * w for w in col_widths)
    lines = [header, sep]
    for row in rows:
        line = " | ".join(str(cell).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i])
                          for i, cell in enumerate(row))
        lines.append(line)
    return "\n".join(lines)
