"""Expresiones mediante AST permitido, sin eval ni parseadores que ejecuten código."""

import ast
import math
import warnings
import numpy as np
import sympy as sp
from scipy.integrate import quad, IntegrationWarning
from scipy.optimize import brentq

X = sp.Symbol("x", real=True)
FUNCTIONS = {
    name: getattr(sp, name)
    for name in (
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "sinh",
        "cosh",
        "tanh",
        "exp",
        "log",
        "sqrt",
        "Abs",
    )
}
FUNCTIONS["abs"] = sp.Abs


def expression(text: str):
    if len(text) > 180:
        raise ValueError("Usá expresiones de hasta 180 caracteres")
    try:
        tree = ast.parse(text.replace("^", "**"), mode="eval")
    except SyntaxError as exc:
        raise ValueError(
            "Expresión inválida. Ejemplo: sin(x) + x^2; usá * para multiplicar."
        ) from exc
    if len(list(ast.walk(tree))) > 90:
        raise ValueError("Expresión demasiado compleja")

    def visit(node, depth=0):
        if depth > 12:
            raise ValueError("Demasiados niveles de operaciones")
        if isinstance(node, ast.Expression):
            return visit(node.body, depth + 1)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if not math.isfinite(node.value) or abs(node.value) > 1e12:
                raise ValueError("Constante fuera de rango")
            return sp.Rational(str(node.value))
        if isinstance(node, ast.Name) and node.id in ("x", "pi", "e", "I"):
            return {"x": X, "pi": sp.pi, "e": sp.E, "I": sp.I}[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand, depth + 1)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left, depth + 1), visit(node.right, depth + 1)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            if isinstance(node.op, ast.Div):
                if b == 0:
                    raise ValueError("División por cero")
                return a / b
            if isinstance(node.op, ast.Pow):
                if b.is_number and (not b.is_real or abs(float(b)) > 100):
                    raise ValueError("Exponente numérico máximo: 100")
                if b.has(sp.Pow):
                    raise ValueError("No se admiten torres de potencias")
                return sp.Pow(a, b)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in FUNCTIONS
            and len(node.args) == 1
            and not node.keywords
        ):
            return FUNCTIONS[node.func.id](visit(node.args[0], depth + 1))
        raise ValueError("Usá números, x, pi, e, I y funciones matemáticas admitidas")

    result = visit(tree)
    if result.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
        raise ValueError("Resultado no finito")
    return result


def real_function(expr):
    raw = sp.lambdify(X, expr, modules="numpy")

    def fn(value):
        try:
            with np.errstate(all="ignore"):
                out = np.asarray(raw(np.asarray(value, dtype=float)), dtype=complex)
        except (ZeroDivisionError, OverflowError, FloatingPointError) as exc:
            raise ValueError(
                "La función no está definida o excede el rango numérico"
            ) from exc
        if np.any(np.abs(out.imag) > 1e-10) or not np.all(np.isfinite(out)):
            raise ValueError("La función no es real y finita en el intervalo indicado")
        return out.real

    return fn


def calculate(text, operation, a=0.0, b=1.0):
    expr = expression(text)
    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError("Límites no finitos")
    if operation == "Evaluar en x = a":
        value = expr.subs(X, sp.Float(a)).evalf(12)
        if value.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
            raise ValueError("La función no está definida en ese punto")
        return f"f({a:g}) = {value}"
    if operation == "Derivada":
        return f"f′(x) = {sp.diff(expr, X)}"
    if operation == "Primitiva":
        value = sp.integrate(expr, X)
        if value.has(sp.Integral):
            return f"No se encontró una primitiva cerrada: {value}. Probá la integral numérica."
        return f"∫ f(x) dx = {value} + C"
    fn = real_function(expr)
    if operation == "Integral numérica [a, b]":
        with warnings.catch_warnings():
            warnings.simplefilter("error", IntegrationWarning)
            try:
                value, error = quad(lambda x: float(fn(x)), a, b, limit=150)
            except IntegrationWarning as exc:
                raise ValueError(
                    "La integración no converge; revisá singularidades y límites"
                ) from exc
        return (
            f"∫ de {a:g} a {b:g} = {value:.12g}\nError absoluto estimado: {error:.3g}"
        )
    if operation == "Raíz en [a, b]":
        if a >= b:
            raise ValueError(
                "La raíz requiere a < b y una función continua con cambio de signo"
            )
        root = brentq(lambda x: float(fn(x)), a, b)
        residual = abs(float(fn(root)))
        if residual > 1e-7:
            raise ValueError(
                "No se verificó una raíz; revisá discontinuidades o la escala de f(x)"
            )
        return f"x ≈ {root:.12g}\nResiduo |f(x)| = {residual:.3g} (método de Brent)"
    raise ValueError("Operación desconocida")


def function_samples(text, a, b):
    if a >= b:
        raise ValueError("El gráfico requiere a < b")
    x = np.linspace(a, b, 1000)
    fn = real_function(expression(text))
    y = np.broadcast_to(fn(x), x.shape).copy()
    return x, y


def matrix_analysis(matrix_text, vector_text):
    try:
        a = np.array(
            [
                [float(x) for x in row.split()]
                for row in matrix_text.strip().splitlines()
            ]
        )
        b = np.array([float(x) for x in vector_text.split()])
    except ValueError as exc:
        raise ValueError(
            "Separá columnas con espacios y filas con saltos de línea"
        ) from exc
    if (
        a.ndim != 2
        or not 1 <= a.shape[0] <= 8
        or a.shape[0] != a.shape[1]
        or b.shape != (a.shape[0],)
    ):
        raise ValueError(
            "A debe ser cuadrada (1 a 8 filas) y b debe tener un valor por fila"
        )
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("Usá valores finitos")
    with np.errstate(over="ignore", invalid="ignore"):
        det = np.linalg.det(a)
    if not np.isfinite(det):
        raise ValueError("Determinante fuera del rango numérico; reescalá la matriz")
    eigen = np.linalg.eigvals(a)
    try:
        solution = np.linalg.solve(a, b)
    except np.linalg.LinAlgError as exc:
        raise ValueError("Sistema singular: no tiene solución única") from exc
    condition = np.linalg.cond(a)
    return (
        f"x = {np.array2string(solution, precision=8)}\n\ndet(A) = {det:.8g}\nAutovalores = {np.array2string(eigen, precision=6)}\nCondición = {condition:.5g}\nResiduo ‖Ax − b‖ = {np.linalg.norm(a @ solution - b):.3g}"
        + ("\nAtención: sistema mal condicionado." if condition > 1e10 else "")
    )


def statistics(text):
    try:
        values = np.array([float(x) for x in text.replace(",", " ").split()])
    except ValueError as exc:
        raise ValueError("Usá valores separados por espacios y punto decimal") from exc
    if len(values) < 2 or len(values) > 100000 or not np.all(np.isfinite(values)):
        raise ValueError("Ingresá entre 2 y 100000 valores finitos")
    if np.max(np.abs(values)) > 1e150:
        raise ValueError("Datos fuera de rango; reescalá las mediciones")
    return f"n = {len(values)}\nMedia = {np.mean(values):.8g}\nMediana = {np.median(values):.8g}\nDesvío muestral (n−1) = {np.std(values, ddof=1):.8g}\nVarianza muestral = {np.var(values, ddof=1):.8g}\nMínimo = {np.min(values):.8g}\nMáximo = {np.max(values):.8g}\nError estándar de la media = {np.std(values, ddof=1) / np.sqrt(len(values)):.8g}"
