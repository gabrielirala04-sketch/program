# Validación de la versión 0.3

Entorno: Debian 13, Python 3.12; interfaz Qt con plataforma `offscreen`. No es una prueba de escritorio nativa de Linux Mint Cinnamon.

## Resultados

- **146 pruebas aprobadas**, sin fallos ni omisiones, en la ejecución completa con ngspice disponible.
- Las 30 herramientas nuevas ejecutaron sus parámetros de ejemplo y produjeron resultados serializables y finitos.
- Verificación con soluciones cerradas de vigas y torsión, identidades de tensiones, balances de energía, casos de cuadratura/EDO y conversiones de unidades.
- Comprobación de ngspice 44.2 frente a la función de transferencia RC y leyes de corrientes/tensiones del emisor común.
- Pruebas de entradas inválidas, dominio de funciones, no convergencia y ausencia explícita del motor SPICE.
- Pruebas de navegación, guardado de resultados como apuntes, exportación CSV y limpieza de resultados al editar parámetros.
- Persistencia y restauración de respaldos de la versión anterior verificadas por la suite existente.
- Instalador local `instalar_linux_mint.sh` ejecutado sin `--sistema`: entorno virtual, instalación editable y comprobación de dependencias satisfactorios.
- Lanzador de usuario creado en una ruta XDG aislada y validado con `desktop-file-validate`. Tras ajustar sus categorías, se repitieron las dos pruebas específicas de lanzadores: aprobadas.
- Wheel 0.3.0 construido, instalado en una ruta independiente e importado desde esa ruta. Ventana con diez secciones y circuito ngspice comprobados.
- Revisión visual de Mi semestre, Rankine y emisor común; tamaño normal y compacto de 1020×700. Se usan paneles desplazables para datos e hipótesis.
- `ruff check --select F`, `git diff --check` y `pip check` satisfactorios.

## Cómo repetir

```bash
.venv/bin/python -m pytest -q
```

Para que las pruebas SPICE se ejecuten, ngspice debe estar en `PATH` o indicarse con `INGENIERIA_LAB_NGSPICE`. Si falta, la prueba de integración se omite explícitamente y el producto muestra que no ejecutó la simulación. En la validación indicada arriba se utilizó un paquete oficial Debian descargado mediante APT con verificación de firmas y sumas, extraído en una ruta local sin modificar paquetes de sistema.

## Límites de lo comprobado

No se ejecutó `sudo apt-get` en Linux Mint ni se probó una sesión Cinnamon real. El instalador contempla las dependencias de Qt y ngspice para Mint y verifica Python 3.11–3.14. No se ejecutaron Qucs-S, CircuitJS, KiCad u Octave para comparar sus interfaces; la investigación usa sus fuentes de documentación publicadas. No se validaron diseños frente a una norma eléctrica específica ni contra equipos de laboratorio físicos.
