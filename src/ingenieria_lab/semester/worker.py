"""Cálculos aislados de la interfaz; el llamador impone tiempo máximo."""

import json
import sys
import warnings
from .registry import run_tool


def main():
    try:
        request = json.load(sys.stdin)
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            data = run_tool(request["key"], request["params"])
        print(json.dumps({"result": data}, ensure_ascii=True, allow_nan=False))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
