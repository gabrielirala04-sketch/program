from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Input:
    key: str
    label: str
    default: object
    minimum: float = -1e9
    maximum: float = 1e9
    integer: bool = False
    options: tuple = ()


@dataclass(frozen=True)
class Tool:
    key: str
    name: str
    subject: str
    kind: str
    inputs: tuple
    description: str
    formula: str
    solve: object


def n(key, label, value, minimum=0, maximum=1e9, integer=False):
    return Input(key, label, value, minimum, maximum, integer)


def text(key, label, value):
    return Input(key, label, value)


def choice(key, label, options):
    return Input(key, label, options[0], options=tuple(options))


def curve(name, x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError(
            "El modelo produjo valores no finitos. Revisá los datos y el dominio."
        )
    return {"name": name, "x": x.tolist(), "y": y.tolist()}


def chart(title, xlabel, ylabel, *curves):
    return {"title": title, "xlabel": xlabel, "ylabel": ylabel, "curves": list(curves)}


def result(metrics, charts=(), headers=(), rows=(), note=""):
    for value in metrics.values():
        if isinstance(value, (float, int)) and not math.isfinite(value):
            raise ValueError("Resultado fuera del rango numérico")
    return {
        "metrics": metrics,
        "charts": list(charts),
        "headers": list(headers),
        "rows": list(rows),
        "note": note,
    }
