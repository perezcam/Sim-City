# Sim-City — Poblado en Evolución

Simulación de eventos discretos (pasos mensuales) para estudiar la evolución poblacional
de una región durante 100 años.

## Requisitos

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Simulación por defecto (500 mujeres, 500 hombres, 100 años)
python main.py

# Personalizado
python main.py --mujeres 200 --hombres 200 --años 100 --seed 42

# Exportar estadísticas y gráficas
python main.py --mujeres 500 --hombres 500 --seed 42 --csv stats.csv

# Solo tabla, sin gráficas
python main.py --no-plot
```

## Estructura del proyecto

```
Sim-City/
├── sim/
│   ├── tables.py       # Tablas de probabilidad del enunciado
│   ├── random_vars.py  # Generadores de variables aleatorias
│   ├── person.py       # Entidad Persona
│   ├── couple.py       # Entidad Pareja
│   └── simulator.py    # Motor de simulación (bucle mensual)
├── main.py             # Punto de entrada CLI
├── visualize.py        # Gráficas matplotlib
└── requirements.txt
```

## Modelo

| Aspecto | Decisión |
|---|---|
| Unidad de tiempo | Mes |
| Horizonte | 100 años (1 200 pasos) |
| Probabilidades de muerte | Anuales → convertidas a mensuales: `1-(1-p)^(1/12)` |
| Probabilidades de embarazo | Mensuales directas |
| Ruptura | Prob. anual 0.2 → mensual: `1-(0.8)^(1/12)` |
| Hijos deseados | Distribución empírica normalizada |
| Duración embarazo | 9 meses fijos |
| Emparejamiento | Barajar listas + iterar secuencialmente |
