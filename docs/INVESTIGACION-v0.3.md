# Investigación aplicada al semestre · Ingeniería Lab 0.3

Consulta: 26 de octubre de 2026. Perfil: Linux Mint Cinnamon; segundo semestre del tercer año de Ingeniería Electromecánica, orientación electrónica. Se priorizan Resistencia de Materiales, Cálculo Numérico, Instalaciones Eléctricas, Mediciones Eléctricas y Electrónicas y Termodinámica. Preparación adicional: Electrónica Analógica.

## Resultado de la investigación

La combinación útil para este perfil es un cuaderno local con cálculos transparentes y casos guiados, más motores científicos existentes donde una fórmula ideal resulta insuficiente. Se integra **CoolProp** para propiedades reales y **ngspice** para dos circuitos originales. Se conservan NumPy, SciPy, SymPy y el laboratorio de señales. Se implementan 30 herramientas nuevas, con entradas editables, supuestos, exportación y resultados guardables como apuntes.

Se consultó documentación primaria de los proyectos en sus repositorios publicados. Los sitios independientes de documentación fueron bloqueados por la política de red de este entorno; se usaron sus fuentes publicadas en GitHub. No se realizaron pruebas de todas las aplicaciones comparadas ni una auditoría de sus últimas versiones. La evaluación de interfaz de otros productos se limita a lo descrito en sus documentos; no se afirma haberlos usado visualmente.

| Referencia | Qué aporta y para qué sirve | Decisión para Ingeniería Lab |
|---|---|---|
| [Qucs-S](https://github.com/ra3xdh/qucs_s) | Captura de esquemas y visualización con ngspice, Xyce y otros motores; declara soporte Linux. | Es una buena herramienta complementaria de electrónica en Mint. Se adopta la separación entre interfaz y motor, sin copiar su código. |
| [ngspice](https://github.com/ngspice/ngspice) | Simulación de circuitos SPICE y modelos activos. | Integrado como proceso local opcional: RC transitorio y emisor común NPN con punto DC y análisis AC. Netlists propios exportables. Motor verificado: ngspice 44.2. |
| [CircuitJS1](https://github.com/sharpie7/circuitjs1) | Simulador en navegador; orienta a experimentar visualmente y exportar circuitos. | Inspira casos de aprendizaje con cambios de parámetros y curvas visibles. No se incorpora ni distribuye su código GPL. |
| [KiCad / Eeschema](https://github.com/KiCad/kicad-doc) | Documenta simulación con ngspice, asignación de modelos, análisis AC/DC/transitorio y exportación de datos. | Complemento para esquemas y modelos de fabricante. Nuestra versión usa circuitos guiados, no un editor CAD. |
| [GNU Octave](https://github.com/gnu-octave/octave) | Lenguaje de cálculo numérico, problemas lineales/no lineales y gráficos, cercano a MATLAB. | Complemento para trabajos extensos de cátedra. El programa presenta métodos acotados con tablas de iteraciones y error. |
| [SciPy](https://github.com/scipy/scipy) | Cuadraturas, interpolación y resolución de EDO; documentación con hipótesis y ejemplos. | Referencias adaptativas para comparar trapecios, Simpson, Euler y RK4. Interpolación baricéntrica y spline natural. |
| [SymPy](https://github.com/sympy/sympy) | Diferenciación simbólica y módulo de vigas con cargas, reacciones, cortante, momento y deformación. | Derivada simbólica en Newton y modelos propios explícitos de vigas, cotejados con soluciones cerradas. |
| [CoolProp](https://github.com/CoolProp/CoolProp) | API PropsSI, pares de estado, saturación, fase, entalpía y entropía. | Integración real para agua y R134a; ciclo Rankine ideal con propiedades reales y trayectorias T–s. Evita inventar tablas de vapor. |

## Fuentes primarias efectivamente consultadas

- [ngspice README](https://raw.githubusercontent.com/ngspice/ngspice/master/README): alcance del motor y antecedentes SPICE/XSPICE.
- [Qucs-S README](https://raw.githubusercontent.com/ra3xdh/qucs_s/current/README.md): motores, plataformas y dependencia de ngspice.
- [CircuitJS1 README](https://raw.githubusercontent.com/sharpie7/circuitjs1/master/README.md): navegador, exportaciones y licencia.
- [Documentación de simulación KiCad](https://raw.githubusercontent.com/KiCad/kicad-doc/master/src/eeschema/eeschema_simulator.adoc): modelos, análisis y exportación. El documento consultado pertenece a ese árbol de fuentes y no garantiza correspondencia con todas las versiones actuales de KiCad.
- [Octave README](https://raw.githubusercontent.com/gnu-octave/octave/default/README): capacidades y plataformas de trabajo.
- [Tutorial de integración SciPy](https://raw.githubusercontent.com/scipy/scipy/main/doc/source/tutorial/integrate.rst): trapecios, Simpson, integración adaptativa y solve_ivp.
- [Documentación Beam de SymPy](https://raw.githubusercontent.com/sympy/sympy/master/doc/src/modules/physics/continuum_mechanics/beam.rst) y documentación del módulo instalado `sympy.physics.continuum_mechanics.beam`: modelos y ejemplos de vigas.
- [CoolProp High-Level API](https://raw.githubusercontent.com/CoolProp/CoolProp/master/Web/coolprop/HighLevelAPI.rst): PropsSI, entradas P,T/P,Q, fase y referencias de entalpía/entropía.

Los enlaces a ramas pueden cambiar con el tiempo; `docs/fuentes-investigacion.json` registra tamaño y SHA256 de los documentos descargados. Se investigaron capacidades y métodos. No se copiaron programas, interfaces o implementaciones GPL al repositorio. Las dependencias conservan sus propias licencias; ngspice se invoca como programa instalado por el usuario.

## Casos implementados por materia

### Resistencia de Materiales — 4 herramientas

1. Viga simplemente apoyada o voladizo, carga puntual en posición editable y carga distribuida uniforme: reacciones, V(x), M(x), flecha y esfuerzo máximo de flexión. Sección rectangular; E configurable.
2. Estado plano y círculo de Mohr: principales, cortante máximo en plano y 3D, Von Mises y ángulo principal.
3. Torsión de eje circular macizo/hueco: J, esfuerzo y giro.
4. Euler: carga crítica, radio de giro y esbeltez.

Casos de verificación: viga con carga central, carga uniforme, voladizo, conservación de fuerzas, torsión y tensión uniaxial. Estos modelos no incluyen elementos finitos, plasticidad, apoyos elásticos ni secciones compuestas.

### Cálculo Numérico — 4 herramientas

1. Bisección, Newton y secante: tabla, residuo, cambio de aproximación y convergencia explícita.
2. Trapecios y Simpson compuestos: tabla de nodos, comparación con quad y errores absolutos.
3. Interpolación polinómica baricéntrica, spline natural y regresión lineal: evaluación, gráfica, pendiente, intercepto y R².
4. Euler y RK4 para una EDO escalar: tabla y comparación con solve_ivp de tolerancia ajustada.

Se conserva el analizador de expresiones por AST permitido, sin `eval` de texto del usuario. Los cálculos se ejecutan fuera de la interfaz con un límite de tiempo. No se afirma que el resultado de referencia sea exacto ni que cualquier función converja.

### Instalaciones Eléctricas — 4 herramientas

1. Caída de tensión con cobre/aluminio, mono/trifásico, temperatura, factor de potencia y reactancia. Curva frente a longitud y sección de tabla por caída únicamente.
2. Compensación de factor de potencia: kvar y capacitancias por rama en estrella/delta.
3. Corriente de diseño y comprobación de Ib≤In≤Iz, con Iz corregida suministrada por el usuario.
4. Cortocircuito simétrico con impedancia equivalente total dada.

Las relaciones son modelos de circuitos, **no una validación de normativa ANDE/IEC ni un dimensionamiento integral**. No se obtuvo documentación normativa suficiente para seleccionar protecciones o ampacidad automáticamente. El límite de caída se ingresa como dato del ejercicio. Por eso se muestran explícitamente los requisitos no evaluados en la propia herramienta. Tensión y frecuencia son editables.

### Mediciones Eléctricas y Electrónicas — 5 herramientas

1. Multímetro: especificación ±(% de lectura + dígitos), límite de error y tipo B rectangular.
2. Carga del voltímetro sobre una fuente con resistencia de Thévenin.
3. Propagación de incertidumbre en un producto con correlación y cobertura.
4. Galga en cuarto de puente de Wheatstone: sensibilidad y curva de transferencia.
5. Muestreo de una senoide: puntos adquiridos, señal original y alias compatible.

Se conservan estadística, RMS, FFT y señales de la versión anterior. No se equipara exactitud de catálogo con incertidumbre total ni se inventan certificados de calibración.

### Termodinámica — 5 herramientas

1. Agua/R134a con CoolProp, entradas P,T o P,x: fase, densidad, volumen específico, h, u y s.
2. Rankine ideal con bomba/turbina isentrópicas y propiedades reales: cuatro estados, balance y trayectorias T–s.
3. Otto aire estándar: estados, calor, trabajo y curvas P–v.
4. Proceso politrópico, incluyendo límite isotérmico n=1: trabajo y P–V.
5. Primera ley en sistema cerrado, convenio de signos y energía interna final.

CoolProp no convierte equipos ideales en máquinas reales. No se modelan pérdidas de presión, eficiencias reales de turbomáquinas, combustión o refrigeración completa en esta versión.

### Preparación de Electrónica Analógica — 8 herramientas

1. Rectificador de media onda/puente con capacitor: formas de onda, media y rizado con descarga RC.
2. BJT con divisor: punto Q, región, recta de carga, gm, rπ y ganancias aproximadas.
3. Operacional inversor/no inversor con recorte estático configurable.
4. RC pasa bajos/altos: Bode de magnitud y fase.
5. Curva de Shockley y temperatura.
6. Regulador Zener con carga: condición de regulación, corrientes y potencias.
7. RC transitorio con ngspice.
8. Emisor común NPN con ngspice: .op y .ac, modelo genérico, acoplamientos y bypass.

No se simula un transistor comercial específico sin su modelo. El cálculo BJT simplificado deja de mostrar un punto Q activo válido cuando detecta saturación. Los límites de salida del operacional no pretenden representar GBW o slew rate. La rectificación didáctica usa caída constante y recarga instantánea; para corrientes de diodo y modelos más completos se recomienda una herramienta SPICE de esquemas como Qucs-S o KiCad.

## Camino de aprendizaje recomendado

- Ahora: usar un ejercicio de cátedra, resolverlo a mano, contrastarlo con el modelo, cambiar una condición y explicar la diferencia en un apunte.
- Antes del próximo semestre: diodo → rectificación → Zener → BJT DC → pequeña señal → operacionales → respuesta en frecuencia.
- Contrastar el mismo circuito aproximado con ngspice y documentar qué supuestos explican la diferencia.
- Llevar cada práctica con parámetros, unidades, resultados y limitaciones a los apuntes; exportar las tablas para el informe de laboratorio.
