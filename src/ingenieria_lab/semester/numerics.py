import warnings
import numpy as np
import sympy as sp
from scipy.integrate import quad, solve_ivp, IntegrationWarning
from scipy.interpolate import BarycentricInterpolator, CubicSpline
from ingenieria_lab.core.mathematics import expression, real_function, X
from .types import Tool, n, text, choice, curve, chart, result

SUBJECT = "Cálculo Numérico"


def roots(p):
    expr = expression(p["expr"])
    fn = real_function(expr)
    df = real_function(sp.diff(expr, X))
    a, b, tol, limit = p["a"], p["b"], p["tol"], int(p["iterations"])
    method = p["method"]
    if a >= b:
        raise ValueError(
            "Usá a < b: intervalo para bisección, semillas a y b para secante; Newton inicia en a"
        )
    fa, fb = float(fn(a)), float(fn(b))
    rows = []
    converged = False
    reason = "Se alcanzó el máximo de iteraciones"
    if method == "Bisección" and np.sign(fa) == np.sign(fb) and fa != 0 and fb != 0:
        raise ValueError("Bisección necesita un cambio de signo o un extremo raíz")
    old = a
    x = a
    for i in range(1, limit + 1):
        if abs(fa) <= tol:
            x = a
        elif method == "Bisección":
            x = b if abs(fb) <= tol else (a + b) / 2
        elif method == "Newton":
            slope = float(df(a))
            if abs(slope) < 1e-14:
                reason = "Derivada nula o demasiado pequeña"
                break
            x = a - fa / slope
        else:
            denominator = fb - fa
            if abs(denominator) < 1e-15:
                reason = "Secante: denominador demasiado pequeño"
                break
            x = b - fb * (b - a) / denominator
        fx = float(fn(x))
        step = abs(x - old)
        rows.append([i, x, fx, step])
        old = x
        if abs(fx) <= tol:
            converged = True
            reason = "Residuo dentro de la tolerancia"
            break
        if method == "Bisección":
            if np.sign(fa) != np.sign(fx):
                b, fb = x, fx
            else:
                a, fa = x, fx
        elif method == "Newton":
            a, fa = x, fx
        else:
            a, fa, b, fb = b, fb, x, fx
    return result(
        {
            "Estado": "Convergió" if converged else "NO convergió",
            "Última aproximación x": x,
            "Residuo |f(x)|": abs(float(fn(x))),
            "Iteraciones": len(rows),
        },
        [
            chart(
                "Convergencia",
                "Iteración",
                "|f(x)|",
                curve("Residuo", [r[0] for r in rows], [abs(r[2]) for r in rows]),
            )
        ]
        if rows
        else [],
        ["i", "x", "f(x)", "|Δx|"],
        rows,
        note=reason
        + ". Se exige residuo pequeño, no solo pasos pequeños. La continuidad y validez del dominio son hipótesis del usuario; puede haber otras raíces.",
    )


def integration(p):
    a, b, N = p["a"], p["b"], int(p["N"])
    if a >= b:
        raise ValueError("Usá a < b")
    if N % 2:
        raise ValueError("Simpson 1/3 requiere un número par de subintervalos N")
    fn = real_function(expression(p["expr"]))
    x = np.linspace(a, b, N + 1)
    y = np.broadcast_to(fn(x), x.shape)
    h = (b - a) / N
    trap = h * (0.5 * y[0] + sum(y[1:-1]) + 0.5 * y[-1])
    simp = h / 3 * (y[0] + y[-1] + 4 * sum(y[1:-1:2]) + 2 * sum(y[2:-1:2]))
    with warnings.catch_warnings():
        warnings.simplefilter("error", IntegrationWarning)
        try:
            reference, err = quad(lambda v: float(fn(v)), a, b, limit=150)
        except IntegrationWarning as exc:
            raise ValueError(
                "La referencia adaptativa no converge; revisá el dominio"
            ) from exc
    return result(
        {
            "Trapecios compuestos": trap,
            "Simpson 1/3 compuesto": simp,
            "Referencia adaptativa quad": reference,
            "Error absoluto trapecios": abs(trap - reference),
            "Error absoluto Simpson": abs(simp - reference),
            "Estimación error de quad": err,
        },
        [chart("Integrando", "x", "f(x)", curve("Nodos", x, y))],
        ["x", "f(x)"],
        np.column_stack((x, y)).tolist(),
        note="La referencia es numérica, no exacta. Se supone una función integrable y suficientemente regular; revisá singularidades.",
    )


def interpolation(p):
    try:
        xs = np.array([float(v) for v in p["xs"].replace(",", " ").split()])
        ys = np.array([float(v) for v in p["ys"].replace(",", " ").split()])
    except ValueError as exc:
        raise ValueError(
            "Ingresá números separados por espacios, con punto decimal"
        ) from exc
    if (
        not 2 <= len(xs) <= 20
        or len(xs) != len(ys)
        or not np.all(np.isfinite(xs))
        or not np.all(np.isfinite(ys))
    ):
        raise ValueError("Usá de 2 a 20 pares finitos x,y")
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    if np.any(np.diff(xs) <= 0):
        raise ValueError("Los nodos x deben ser distintos")
    if not xs[0] <= p["at"] <= xs[-1]:
        raise ValueError(
            "El punto a evaluar debe estar entre los nodos; no extrapolamos"
        )
    x = np.linspace(xs[0], xs[-1], 500)
    poly = BarycentricInterpolator(xs, ys, random_state=0)
    spline = CubicSpline(xs, ys, bc_type="natural")
    coeff = np.polynomial.polynomial.polyfit(xs, ys, 1)
    fitted = coeff[0] + coeff[1] * xs
    total = np.sum((ys - np.mean(ys)) ** 2)
    return result(
        {
            "Polinomio en x elegido": float(poly(p["at"])),
            "Spline natural en x elegido": float(spline(p["at"])),
            "Regresión: intercepto": coeff[0],
            "Regresión: pendiente": coeff[1],
            "Regresión: R²": float(1 - np.sum((ys - fitted) ** 2) / total)
            if total > 0
            else "No definido para y constante",
        },
        [
            chart(
                "Interpolación y ajuste",
                "x",
                "y",
                curve("Polinomio interpolante", x, poly(x)),
                curve("Spline natural", x, spline(x)),
                curve("Recta mínimos cuadrados", x, coeff[0] + coeff[1] * x),
                curve("Nodos", xs, ys),
            )
        ],
        note="Interpolar pasa por los nodos; ajustar por mínimos cuadrados generalmente no. El spline natural impone segunda derivada nula en los extremos. Polinomios de grado alto pueden oscilar.",
    )


def ode(p):
    a, b, N = p["a"], p["b"], int(p["N"])
    if a >= b:
        raise ValueError("Usá x inicial < x final")
    Y = sp.Symbol("y", real=True)
    expr = expression(p["expr"], {"y": Y})
    raw = sp.lambdify((X, Y), expr, "numpy")

    def f(x, y):
        with np.errstate(all="ignore"):
            val = complex(raw(x, y))
        if not np.isfinite(val) or abs(val.imag) > 1e-10:
            raise ValueError("La EDO sale del dominio real y finito")
        return val.real

    x = np.linspace(a, b, N + 1)
    h = (b - a) / N
    euler = np.zeros(N + 1)
    rk = euler.copy()
    euler[0] = rk[0] = p["y0"]
    for i in range(N):
        euler[i + 1] = euler[i] + h * f(x[i], euler[i])
        k1 = f(x[i], rk[i])
        k2 = f(x[i] + h / 2, rk[i] + h * k1 / 2)
        k3 = f(x[i] + h / 2, rk[i] + h * k2 / 2)
        k4 = f(x[i] + h, rk[i] + h * k3)
        rk[i + 1] = rk[i] + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    ref = solve_ivp(
        lambda t, y: [f(t, y[0])], (a, b), [p["y0"]], t_eval=x, rtol=1e-10, atol=1e-12
    )
    if not ref.success:
        raise ValueError("La solución adaptativa no convergió: " + ref.message)
    return result(
        {
            "Paso h": h,
            "Euler final": euler[-1],
            "RK4 final": rk[-1],
            "Referencia final": ref.y[0, -1],
            "Error final Euler": abs(euler[-1] - ref.y[0, -1]),
            "Error final RK4": abs(rk[-1] - ref.y[0, -1]),
        },
        [
            chart(
                "Soluciones",
                "x",
                "y",
                curve("Euler", x, euler),
                curve("RK4", x, rk),
                curve("Referencia adaptativa", x, ref.y[0]),
            )
        ],
        ["x", "Euler", "RK4", "Referencia"],
        np.column_stack((x, euler, rk, ref.y[0])).tolist(),
        note="EDO escalar y′=f(x,y); métodos explícitos de paso fijo. La referencia también es numérica. Una EDO rígida puede requerir métodos implícitos.",
    )


TOOLS = [
    Tool(
        "roots",
        "Raíces: bisección, Newton y secante",
        SUBJECT,
        "Laboratorio",
        (
            text("expr", "f(x)", "x^3-x-2"),
            choice("method", "Método", ["Bisección", "Newton", "Secante"]),
            n("a", "a / semilla inicial", 1, -1e6, 1e6),
            n("b", "b / segunda semilla", 2, -1e6, 1e6),
            n("tol", "Tolerancia absoluta de f(x)", 1e-8, 1e-12, 1),
            n("iterations", "Máximo de iteraciones", 80, 1, 200, True),
        ),
        "Tabla de iteraciones y residuo. Newton usa derivada simbólica.",
        "Bisección: m=(a+b)/2 · Newton: x−f/f′",
        roots,
    ),
    Tool(
        "integration",
        "Integración: trapecios y Simpson",
        SUBJECT,
        "Laboratorio",
        (
            text("expr", "f(x)", "sin(x)"),
            n("a", "a", 0, -1e6, 1e6),
            n("b", "b", 3.1415926536, -1e6, 1e6),
            n("N", "Subintervalos N (par)", 20, 2, 1000, True),
        ),
        "Comparación de cuadraturas compuestas con referencia adaptativa y tabla de nodos.",
        "Trapecios O(h²), Simpson O(h⁴) para funciones suficientemente suaves",
        integration,
    ),
    Tool(
        "interpolation",
        "Interpolación y regresión lineal",
        SUBJECT,
        "Laboratorio",
        (
            text("xs", "Nodos x separados por espacios", "0 1 2 3"),
            text("ys", "Datos y separados por espacios", "0 1 4 9"),
            n("at", "Evaluar en x", 1.5, -1e9),
        ),
        "Polinomio baricéntrico, spline cúbico natural y mínimos cuadrados lineales.",
        "p(xi)=yi · ajuste y≈a+bx",
        interpolation,
    ),
    Tool(
        "ode",
        "EDO: Euler y Runge–Kutta 4",
        SUBJECT,
        "Laboratorio",
        (
            text("expr", "f(x,y), donde y′=f(x,y)", "-2*y"),
            n("a", "x inicial", 0, -1e6, 1e6),
            n("b", "x final", 2, -1e6, 1e6),
            n("y0", "y inicial", 1, -1e9),
            n("N", "Pasos", 40, 2, 2000, True),
        ),
        "Comparación explícita con solve_ivp como referencia numérica.",
        "Euler: y[n+1]=y[n]+h f(x[n],y[n])",
        ode,
    ),
]
