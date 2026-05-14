# Sim-City — Poblado en Evolucion

Simulacion de eventos discretos con pasos mensuales para estudiar la evolucion
poblacional durante 100 anos. El sistema modela mortalidad, formacion y ruptura
de parejas, embarazos y nacimientos, y registra estadisticas agregadas por ano.

## Estado actual del sistema

La rama `main` contiene una implementacion CLI basada en:

- `main.py`: punto de entrada y argumentos de ejecucion.
- `sim/simulator.py`: motor mensual (7 fases por mes).
- `sim/tables.py`: tablas de probabilidades del modelo.
- `sim/random_vars.py`: utilidades de muestreo aleatorio.
- `visualize.py`: generacion de graficas con Matplotlib.

No hay dashboard Streamlit activo en esta rama (`app.py` no forma parte del estado actual).

## Requisitos

- Python 3.10+
- Dependencias de `requirements.txt`

Instalacion:

```bash
pip install -r requirements.txt
```

## Uso

Simulacion por defecto:

```bash
python main.py
```

Simulacion personalizada:

```bash
python main.py --mujeres 500 --hombres 500 --años 100 --seed 42
```

Guardar estadisticas en CSV:

```bash
python main.py --mujeres 500 --hombres 500 --años 100 --seed 42 --csv e2_stats.csv
```

Ejecutar sin graficas:

```bash
python main.py --mujeres 500 --hombres 500 --años 100 --seed 42 --no-plot
```

## Argumentos de `main.py`

- `--mujeres` (int, default `500`)
- `--hombres` (int, default `500`)
- `--años` (int, default `100`)
- `--seed` (int, default `None`)
- `--csv` (str, opcional)
- `--no-plot` (flag)

## Funcionamiento del motor

Cada mes de simulacion ejecuta:

1. Envejecer personas (+1 mes)
2. Evaluar muertes
3. Evaluar rupturas
4. Actualizar tiempo de soledad
5. Formar parejas
6. Evaluar embarazos
7. Procesar nacimientos

Cada 12 meses se registra un snapshot anual con:

- `population`, `men`, `women`
- `couples`, `single`
- `births`, `deaths`
- `couples_formed`, `breakups`
- `age_groups` (`0-12`, `12-45`, `45-76`, `76+`)
- `avg_age`

## Experimentos realizados

Los experimentos base del proyecto variaron tamano inicial y semilla, con
horizonte de 100 anos:

- E1: 100 mujeres + 100 hombres, `seed=0`
- E2: 500 mujeres + 500 hombres, `seed=42`
- E3: 1000 mujeres + 1000 hombres, `seed=7`
- E4: 500 mujeres + 500 hombres, `seed=0` (control de reproducibilidad)

Resultados reportados para E1-E3 (escenario de referencia del informe):

| Experimento | N inicial | Pico | Ano pico | Extincion | Nacidos | Muertos | Poblacion final |
|---|---:|---:|---:|---|---:|---:|---:|
| E1 | 200 | 209 | 6 | No en 100 anos | 151 | 243 | 108 |
| E2 | 1000 | 1046 | 12 | No en 100 anos | 1361 | 1465 | 896 |
| E3 | 2000 | 2079 | 11 | No en 100 anos | 2535 | 2803 | 1732 |

Lecturas principales:

- Hay una caida inicial fuerte por la distribucion de edades de arranque.
- En el horizonte de 100 anos se observa descenso demografico lento, no colapso inmediato.
- Los escenarios mayores (E3) amortiguan mejor la variabilidad relativa.

Figuras asociadas en `informe/figures/`:

- `E1_100x100.png`
- `E2_500x500.png`
- `E3_1000x1000.png`

## Reproducir experimentos

```bash
python main.py --mujeres 100 --hombres 100 --años 100 --seed 0 --no-plot
python main.py --mujeres 500 --hombres 500 --años 100 --seed 42 --no-plot
python main.py --mujeres 1000 --hombres 1000 --años 100 --seed 7 --no-plot
python main.py --mujeres 500 --hombres 500 --años 100 --seed 0 --no-plot
```

## Estructura del proyecto

```text
Sim-City/
├── sim/
│   ├── __init__.py
│   ├── couple.py
│   ├── person.py
│   ├── random_vars.py
│   ├── simulator.py
│   └── tables.py
├── informe/
│   ├── README_informe.md
│   ├── informe.tex
│   └── figures/
├── main.py
├── visualize.py
├── requirements.txt
└── README.md
```
