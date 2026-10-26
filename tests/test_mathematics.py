import json
import subprocess
import sys
import numpy as np
import pytest
from ingenieria_lab.core.mathematics import (
    X,
    expression,
    calculate,
    function_samples,
    matrix_analysis,
    statistics,
)


@pytest.mark.parametrize(
    "text",
    [
        "__import__('os').system('id')",
        "x.__class__",
        "[x for x in (1,2)]",
        "open('x')",
        "lambda:1",
        "2**1000",
        "1/0",
        "float('nan')",
    ],
)
def test_expression_rejects_code_and_invalid_values(text):
    with pytest.raises(ValueError):
        expression(text)


def test_exact_symbolic_results():
    assert expression("sin(pi/2)+x^2") == 1 + X**2
    assert "3*x**2" in calculate("x^3", "Derivada")
    assert "x**3/3" in calculate("x^2", "Primitiva")
    assert "I" in calculate("sqrt(-1)", "Evaluar en x = a")


def test_integral_root_and_constant_plot():
    assert "= 2\n" in calculate("sin(x)", "Integral numérica [a, b]", 0, np.pi)
    result = calculate("x^2-2", "Raíz en [a, b]", 0, 2)
    assert "1.41421356237" in result
    x, y = function_samples("3", -1, 1)
    assert len(x) == 1000 and np.all(y == 3)


def test_discontinuity_not_reported_as_root():
    with pytest.raises(ValueError):
        calculate("1/x", "Raíz en [a, b]", -1, 1)


def test_invalid_domain_and_singular_matrix():
    with pytest.raises(ValueError):
        function_samples("sqrt(x)", -1, 1)
    with pytest.raises(ValueError):
        matrix_analysis("1 2\n2 4", "3 6")
    with pytest.raises(ValueError):
        matrix_analysis("1 2\n3", "1 2")


def test_matrix_and_statistics_reference():
    text = matrix_analysis("2 1\n1 3", "5 7")
    assert "[1.6 1.8]" in text and "det(A) = 5" in text
    text = statistics("1 2 3")
    assert "Media = 2" in text and "Varianza muestral = 1" in text


def test_math_subprocess_protocol():
    result = subprocess.run(
        [sys.executable, "-m", "ingenieria_lab.core.math_worker"],
        input=json.dumps({"text": "x^2", "operation": "Derivada", "a": 0, "b": 1}),
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert json.loads(result.stdout)["result"]["text"] == "f′(x) = 2*x"
