# Prácticas guiadas del semestre

Estos ejemplos se pueden ejecutar sin archivos externos. Los resultados de referencia no sustituyen el programa de la cátedra.

## 1. Resistencia: comparar apoyos

En **Vigas**, usar L=2 m, F=1000 N, a=1 m, q=0, b=50 mm, h=100 mm, E=200 GPa y apoyos simples.

- I=4.1666667×10⁻⁶ m⁴.
- Reacciones: 500 N en cada apoyo.
- Momento máximo: 500 N·m.
- Flecha central: 0.2 mm.
- Tensión máxima de flexión: 6 MPa.

Duplicá la altura de la sección: I se multiplica por ocho y la flecha se divide por ocho. Cambiá a voladizo y colocá a=L: verificá FL³/(3EI) para la flecha del extremo. Conservá el convenio de signos al comparar con tus apuntes.

## 2. Numérico: observar el error

En **Raíces**, usá f(x)=x²−2, a=1, b=2, tolerancia 10⁻⁸. Compará bisección, Newton y secante. La raíz positiva es aproximadamente 1.41421356237.

En **Integración**, usá x³ entre 0 y 1, N=10. Simpson debe producir 0.25 salvo redondeo. Con N=20, el error del trapecio debe ser aproximadamente la cuarta parte.

En **EDO**, usá y′=−2y, y(0)=1, intervalo 0 a 2, N=40. La solución exacta final es exp(−4). Compará errores de Euler y RK4 y después repetí con N=80.

## 3. Instalaciones: separar cálculo de cumplimiento

En **Caída**, elegí monofásico, cobre, V=220 V, I=20 A, longitud de ida=30 m, S=4 mm², cosφ=1, temperatura=20 °C y X=0.

- ΔV = 2×20×30×0.017241/4 = 5.1723 V.
- Caída ≈ 2.351 %.

Aumentá la temperatura a 70 °C. Observá el aumento de resistencia. La sección por caída solo evalúa ese criterio; para una entrega normativa necesitás Iz corregida y las demás comprobaciones indicadas por tu cátedra.

## 4. Mediciones: construir un presupuesto simple

En **Multímetro**, ingresá lectura=12, exactitud=0.5 %, dígitos=2 y resolución=0.01, todo en voltios.

- Límite de error: ±0.08 V.
- Tipo B rectangular: 0.08/√3 ≈ 0.04619 V.

Ese u no incluye repetibilidad, carga, temperatura u otras fuentes. En **Efecto de carga**, probá fuente de 10 V con Rs=1 kΩ y voltímetro de 1 kΩ: la lectura es 5 V. Después aumentá Rv a 10 MΩ.

En **Muestreo**, f=70 Hz y fs=100 Hz da alias aparente de 30 Hz. Las muestras coinciden aunque la señal continua sea distinta.

## 5. Termodinámica: propiedades y balances

En **Propiedades**, seleccioná Water, presión y calidad, P=101.325 kPa y calidad=0. La temperatura debe estar cerca de 100 °C. Cambiá calidad a 1 y compará entalpía. La diferencia representa calor latente a esa presión.

En **Rankine**, usá 10 kPa de condensador, 8000 kPa de caldera y 480 °C de entrada a turbina. Verificá que calor entrante menos saliente sea trabajo neto, y que las etapas idealizadas de bomba y turbina mantengan entropía. Explorá la calidad al final de la expansión.

En **Politrópico**, P1=100 kPa, V1=1 m³, V2=2 m³ y n=1: W=100 ln(2)=69.3147 kJ. Con n=0, W=100 kJ.

## 6. Electrónica: del modelo ideal a SPICE

- **Rectificador:** compará media onda y puente, con 12 V RMS, 50 Hz y carga de 1 kΩ. Duplicá C=470 µF y observá el rizado. No interpretes la recarga ideal instantánea como corriente de diodo física.
- **BJT:** usá los valores iniciales y comprobá la ley de corrientes de la base y la recta de carga. Aumentá RC hasta salir de activo: el programa deja de presentar un punto Q activo válido.
- **Operacional:** ganancia inversora −10, entrada de 1.5 V pico y salida limitada a ±10 V. Se observa recorte; reducí amplitud para recuperarla sin recorte.
- **Filtro RC:** R=10 kΩ, C=10 nF: fc≈1591.55 Hz. El eje Bode muestra log10(f/Hz), por ejemplo 3 representa 1000 Hz.
- **Ngspice RC:** R=1 kΩ, C=1 µF, f=100 Hz, entrada de 1 V pico. En régimen permanente, salida pico ≈ 1/√(1+(2πfRC)²) ≈ 0.8467 V.
- **Ngspice BJT:** guardá el punto DC y Bode. Compará con el BJT simplificado y explicá las diferencias de VBE, efecto Early, capacitores, carga y modelo. El análisis AC es pequeña señal, no comprueba recorte de una señal grande.

Guardá cada resultado con **Guardar en apuntes**. Para informes, exportá el gráfico o la tabla de cálculo visible a CSV. Los datos de distintos gráficos se exportan por separado, conservando sus unidades.
