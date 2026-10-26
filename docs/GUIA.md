# Guía de herramientas generales (conservadas de v0.2)

Para los nuevos laboratorios de v0.3, consultá [Prácticas del semestre](PRACTICAS-v0.3.md) y [la investigación](INVESTIGACION-v0.3.md).

## Calculadora matemática

Usá punto decimal y multiplicación explícita: `2*x`, no `2x`. `^` o `**` indican potencia. `log` es logaritmo natural; los ángulos son radianes. Constantes: `pi`, `e`, `I` (unidad imaginaria).

| Objetivo | Expresión | Operación y parámetros | Resultado de referencia |
|---|---|---|---|
| Derivar | `x^3` | Derivada | `3*x**2` |
| Integrar | `sin(x)` | Integral numérica, a=0, b=3.14159265 | aproximadamente 2 |
| Buscar raíz | `x^2-2` | Raíz, a=0, b=2 | 1.41421356237 |
| Complejos | `sqrt(-1)` | Evaluar | I |
| Gráfico | `exp(-x)*sin(5*x)` | Graficar, a=0, b=5 | oscilación amortiguada |

Para raíces se supone continuidad y cambio de signo. No se garantiza encontrar todas las raíces. Un residuo pequeño verifica el punto encontrado. Los gráficos rechazan valores complejos o no finitos en las muestras del intervalo; separá dominios con singularidades. Una primitiva puede quedar sin resolver. Los cálculos simbólicos se ejecutan en un proceso con límite de 8 segundos para evitar bloquear la aplicación.

En matrices, escribí una fila por línea y columnas con espacios. Por ejemplo A=`2 1` / `1 3`, b=`5 7` produce x=`1.6 1.8`. Se informa condición para detectar sensibilidad al error. Un sistema singular no tiene una solución única mediante este método.

Estadística usa desvío y varianza **muestrales**, divisor n−1. Los datos deben usar la misma unidad. El error estándar mostrado es s/√n; no constituye por sí solo un intervalo de confianza.

## Circuitos, control y mecánica

| Modelo | Condiciones y salida |
|---|---|
| RC | Capacitor descargado, escalón ideal, salida Vc. A un tiempo RC alcanza 63.2 % del cambio. |
| RLC transitorio | R, L y C en serie; salida sobre C; energía inicial cero. Ventana temporal adaptada al amortiguamiento. |
| RLC en CA | Estado estacionario sinusoidal. Entrada RMS; curvas instantáneas. La corriente y tensión conservan sus propias unidades en la leyenda y comparten escala numérica. |
| Masa–resorte | Vibración libre, desplazamiento inicial ajustable y velocidad inicial cero. Sin fuerza externa. |
| Control | Sistema de segundo orden, entrada escalón unitario, ganancia K y condiciones iniciales cero. |

Los gráficos permiten zoom y desplazamiento. Cada exportación CSV corresponde a la **última simulación exitosa**; si una simulación falla se deshabilita su dato exportable. Si editás parámetros, volvé a simular antes de exportar.

## Laboratorio de señales

La amplitud es **pico**, no pico a pico ni RMS. Para una senoide sin offset, RMS = A/√2 cuando la ventana cubre ciclos completos. Con offset D, RMS ideal = √(D²+A²/2).

La FFT unilateral muestra amplitud pico usando ventana rectangular, con DC y Nyquist sin duplicar. Un número no entero de períodos provoca fuga espectral. La frecuencia de muestreo debe superar el doble de la fundamental; para representar armónicos de ondas cuadradas y de sierra hacen falta tasas mucho mayores. La duración y tasa determinan el número de muestras, limitado a dos millones.

## Herramientas y unidades

- Ohm y divisor: resistencias ideales; el divisor no tiene carga.
- Operacionales: salidas ideales, sin límites de rieles ni ancho de banda.
- Potencia trifásica: sistema equilibrado, tensión y corriente de línea RMS; Q es magnitud.
- Motor: polos pares; el deslizamiento negativo es compatible con régimen generador.
- Sensor: escala lineal nominal de 4–20 mA.
- ADC: unipolar, n bits enteros, Vref positiva, LSB=Vref/2ⁿ; el extremo superior se limita al código máximo.
- Esfuerzo axial: sección uniforme, elasticidad lineal; E en GPa y área en mm².
- Viga: simplemente apoyada, carga puntual central, Euler–Bernoulli; I en cm⁴, no momento polar.
- Bomba: densidad, caudal en L/s y altura total; rendimiento mecánico-hidráulico, sin rendimiento adicional del motor.
- Continuidad: velocidad media en tubería circular.
- Calor: capacidad específica constante, sin cambios de fase.
- Carnot: temperaturas absolutas, foco caliente mayor al frío.
- Incertidumbre: suma de magnitudes independientes, mismas unidades y sensibilidades unitarias. Para productos y cocientes se requiere propagación diferente.

## Apuntes, agenda y respaldo

Los apuntes son texto editable compatible con Markdown, sin renderizador de ecuaciones ni adjuntos PDF. No se suministraron los archivos de las carpetas mostradas: el catálogo usa sus nombres, no su contenido. Podés copiar enlaces, referencias y desarrollos propios en los apuntes.

Los estados de materias se guardan explícitamente. La agenda permite completar, reabrir y eliminar tareas. Las fechas corresponden al calendario del equipo.

La restauración reemplaza todos los datos de estudio después de validar el archivo y confirmar. Antes se crea `antes-de-restaurar-*.json` junto a la base. Si la validación falla, los datos actuales permanecen intactos. Guardá respaldos también fuera de esa carpeta para cubrir pérdida del equipo.
