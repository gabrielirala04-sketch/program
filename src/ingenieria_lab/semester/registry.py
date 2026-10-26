import math
from . import mechanics, electrical, numerics, thermodynamics, analog, spice

TOOLS = [
    *mechanics.TOOLS,
    *numerics.TOOLS,
    *electrical.TOOLS,
    *thermodynamics.TOOLS,
    *analog.TOOLS,
    *spice.TOOLS,
]
BY_KEY = {tool.key: tool for tool in TOOLS}
SUBJECTS = list(dict.fromkeys(tool.subject for tool in TOOLS))


def run_tool(key, params):
    tool = BY_KEY[key]
    if set(params) != {field.key for field in tool.inputs}:
        raise ValueError("Faltan parámetros o sobran campos")
    for field in tool.inputs:
        value = params[field.key]
        if field.options:
            if value not in field.options:
                raise ValueError("Opción desconocida: " + field.label)
        elif isinstance(field.default, str):
            if not isinstance(value, str) or not value.strip() or len(value) > 600:
                raise ValueError("Texto vacío o demasiado largo: " + field.label)
        elif (
            not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not field.minimum <= value <= field.maximum
        ):
            raise ValueError("Valor fuera de rango: " + field.label)
        elif field.integer and value != int(value):
            raise ValueError("Se requiere un entero: " + field.label)
    if key == "diode" and params["lo"] >= params["hi"]:
        raise ValueError("La tensión inicial debe ser menor que la final")
    return tool.solve(params)
