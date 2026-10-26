"""Proceso descartable para limitar el tiempo del cálculo simbólico."""

import json
import sys
from ingenieria_lab.core.mathematics import calculate, function_samples


def main():
    request = json.load(sys.stdin)
    try:
        if request["operation"] == "Graficar":
            x, y = function_samples(request["text"], request["a"], request["b"])
            result = {"x": x.tolist(), "y": y.tolist()}
        else:
            result = {"text": calculate(**request)}
        print(json.dumps({"result": result}, allow_nan=False))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))


if __name__ == "__main__":
    main()
