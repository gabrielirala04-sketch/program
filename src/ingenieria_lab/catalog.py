"""Materias transcritas de las imágenes; los bloques no son correlatividades."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Subject:
    name: str
    block: int
    area: str
    topics: str


SUBJECTS = [
    Subject(*row)
    for row in [
        (
            "Álgebra Lineal",
            1,
            "Matemática",
            "Matrices, determinantes, sistemas lineales, espacios vectoriales y autovalores.",
        ),
        (
            "Cálculo II",
            1,
            "Matemática",
            "Integrales, técnicas de integración, series y aplicaciones geométricas.",
        ),
        (
            "Dibujo Técnico",
            1,
            "Diseño",
            "Proyecciones, cortes, acotación, tolerancias y lectura de planos.",
        ),
        (
            "Física I",
            1,
            "Física",
            "Cinemática, dinámica, trabajo, energía y conservación del momento.",
        ),
        (
            "Química",
            1,
            "Física",
            "Estequiometría, soluciones, equilibrio, electroquímica y corrosión.",
        ),
        (
            "Cálculo III",
            2,
            "Matemática",
            "Funciones multivariables, gradiente, integrales múltiples y campos vectoriales.",
        ),
        (
            "Física II",
            2,
            "Física",
            "Oscilaciones, ondas y fenómenos térmicos; contrastar con el programa de cátedra.",
        ),
        (
            "Mecánica Racional",
            2,
            "Mecánica",
            "Estática, cuerpos rígidos, cinemática y dinámica de sistemas.",
        ),
        (
            "Ecuaciones Diferenciales",
            2,
            "Matemática",
            "EDO de primer y segundo orden, Laplace, sistemas y condiciones iniciales.",
        ),
        (
            "Circuitos eléctricos",
            3,
            "Electricidad",
            "Kirchhoff, Thévenin, Norton, transitorios, fasores y potencia en CA.",
        ),
        (
            "Estadística",
            3,
            "Matemática",
            "Estadística descriptiva, probabilidad, distribuciones e inferencia.",
        ),
        (
            "Física III",
            3,
            "Física",
            "Electricidad, magnetismo y óptica; contrastar con el programa de cátedra.",
        ),
        (
            "Mecánica de Fluidos",
            3,
            "Mecánica",
            "Continuidad, Bernoulli, pérdidas de carga y flujo interno.",
        ),
        (
            "Cálculo numérico",
            4,
            "Matemática",
            "Raíces, interpolación, integración numérica, sistemas y error.",
        ),
        (
            "Instalaciones Eléctricas",
            4,
            "Electricidad",
            "Cargas, conductores, caída de tensión, protecciones y puesta a tierra.",
        ),
        (
            "Mediciones Eléctricas",
            4,
            "Electricidad",
            "Instrumentos, incertidumbre, valor eficaz y adquisición de señales.",
        ),
        (
            "Resistencia de Materiales",
            4,
            "Mecánica",
            "Tensión, deformación, flexión, torsión y diagramas de esfuerzos.",
        ),
        (
            "Termodinámica",
            4,
            "Energía",
            "Balances de energía, propiedades, entropía y ciclos térmicos.",
        ),
        (
            "Electrónica I",
            5,
            "Electrónica",
            "Diodos, rectificadores, BJT, MOSFET y polarización.",
        ),
        (
            "Estabilidad Aplicada a las Máquinas",
            5,
            "Mecánica",
            "Vibraciones, equilibrio, esfuerzos y estabilidad mecánica.",
        ),
        (
            "Máquinas Eléctricas",
            5,
            "Electricidad",
            "Transformadores, máquinas de CC, inducción y máquinas síncronas.",
        ),
        (
            "Máquinas Térmicas",
            5,
            "Energía",
            "Ciclos de potencia, motores, turbinas e intercambiadores.",
        ),
        (
            "Redes Industriales",
            5,
            "Electrónica",
            "Protocolos, topologías, buses, comunicación y diagnóstico industrial.",
        ),
        (
            "Tecnología y Procesos de Materiales",
            5,
            "Diseño",
            "Materiales, tratamientos, manufactura y selección de procesos.",
        ),
        (
            "Distribución",
            6,
            "Electricidad",
            "Redes de distribución, demanda, pérdidas y regulación de tensión.",
        ),
        (
            "Electrónica II",
            6,
            "Electrónica",
            "Amplificadores, realimentación, respuesta en frecuencia y filtros.",
        ),
        (
            "Máquinas Hidráulicas I",
            6,
            "Mecánica",
            "Bombas, curvas características, altura y potencia hidráulica.",
        ),
        (
            "Máquinas térmicas II",
            6,
            "Energía",
            "Ciclos avanzados, refrigeración y rendimiento de sistemas térmicos.",
        ),
        (
            "Organización de Empresas",
            6,
            "Gestión",
            "Planificación, costos, gestión de proyectos y organización industrial.",
        ),
        (
            "Sensores y Actuadores",
            6,
            "Electrónica",
            "Transductores, acondicionamiento, calibración y actuadores.",
        ),
        (
            "Electrónica III",
            7,
            "Electrónica",
            "Electrónica aplicada, sistemas digitales y potencia; adaptar a la cátedra.",
        ),
        (
            "Gestión de Calidad",
            7,
            "Gestión",
            "Control estadístico, trazabilidad, procesos y mejora continua.",
        ),
        (
            "Máquinas Hidráulicas II",
            7,
            "Mecánica",
            "Turbomáquinas, similitud, cavitación y selección de equipos.",
        ),
        (
            "Proyecto Final",
            7,
            "Gestión",
            "Requisitos, diseño, prototipos, validación y documentación técnica.",
        ),
        (
            "Seguridad e Higiene",
            7,
            "Gestión",
            "Identificación de peligros, prevención y seguridad en laboratorios.",
        ),
        (
            "Sistemas Automáticos",
            7,
            "Electrónica",
            "Modelado, funciones de transferencia, estabilidad y control.",
        ),
        (
            "Electrónica IV",
            8,
            "Electrónica",
            "Integración de sistemas electrónicos; adaptar al programa de cátedra.",
        ),
        (
            "Ing. Legal",
            8,
            "Gestión",
            "Marco profesional, contratos, responsabilidades y normativa aplicable.",
        ),
        (
            "Transmisión de E",
            8,
            "Electricidad",
            "Líneas de transmisión de energía, parámetros, pérdidas y operación.",
        ),
    ]
]
SUBJECT_NAMES = [s.name for s in SUBJECTS]
AREAS = sorted({s.area for s in SUBJECTS})
GUIDES = {
    "Matemática": (
        "Calculadora",
        "Comprobá dominio y unidades. Contrastá resultados simbólicos con valores numéricos.",
        "Ax = b · f′(x) · ∫ f(x) dx",
    ),
    "Electricidad": (
        "Simuladores",
        "Dibujá el circuito, elegí referencias y distinguí valores pico de valores RMS.",
        "V = RI · P = VI cos φ · Z = R + j(ωL − 1/ωC)",
    ),
    "Electrónica": (
        "Simuladores",
        "Separá el modelo ideal de las limitaciones reales: saturación, ancho de banda y tolerancias.",
        "fc = 1/(2πRC) · Av = 1 + Rf/Rg · τ = RC",
    ),
    "Mecánica": (
        "Herramientas",
        "Armá el diagrama de cuerpo libre. Usá SI y verificá las condiciones de apoyo.",
        "ΣF = ma · σ = F/A · Q = Av · Ph = ρgQH",
    ),
    "Energía": (
        "Herramientas",
        "Definí el volumen de control y el convenio de signos. Usá kelvin en rendimientos ideales.",
        "ΔU = Q − W · η = W/Qin · ηCarnot = 1 − Tc/Th",
    ),
    "Física": (
        "Calculadora",
        "Identificá hipótesis, conservaciones y cifras significativas antes de sustituir valores.",
        "F = ma · Ec = mv²/2 · n = m/M",
    ),
    "Diseño": (
        "Apuntes",
        "Registrá normas usadas, revisiones, tolerancias y decisiones de diseño.",
        "Escala = longitud dibujada / longitud real",
    ),
    "Gestión": (
        "Agenda",
        "Convertí entregables en tareas con fecha y evidencia de validación.",
        "Planificar → ejecutar → verificar → mejorar",
    ),
}
