# Sim-City — Poblado en Evolución

> **Proyecto 6** — Simulación basada en Eventos Discretos  
> Facultad de Matemática y Computación, Universidad de La Habana  
> Camilo Humberto Pérez Fleita · Grupo C312 · Ciencia de la Computación

Simulación de eventos discretos con pasos mensuales (1 200 iteraciones = 100 años)
para estudiar la evolución demográfica de una población: mortalidad, formación de
parejas, embarazos, nacimientos y árbol genealógico.

🔗 **Repositorio:** https://github.com/perezcam/Sim-City

---

## Instalación

```bash
git clone https://github.com/perezcam/Sim-City.git
cd Sim-City
pip install -r requirements.txt
```

**Dependencias:** `matplotlib >= 3.7` · `networkx >= 3.0` · `streamlit >= 1.30`

---

## Modos de uso

### Simulación única
```bash
python3 main.py --mujeres 500 --hombres 500 --años 100 --seed 42
```

### Simulación + exportar CSV y figura
```bash
python3 main.py --mujeres 500 --hombres 500 --seed 42 --csv stats.csv --save-fig resultados.png
```

### Modo de mortalidad anual (alternativo)
```bash
python3 main.py --mujeres 500 --hombres 500 --death-mode annual
```

### Motor FEL fuerte (next-event por entidad)
```bash
python3 main.py --mujeres 500 --hombres 500 --sim-mode calendar_strong
```

### Monte Carlo (N corridas independientes)
```bash
python3 main.py --mujeres 500 --hombres 500 --runs 30
```

### Análisis de sensibilidad
```bash
python3 main.py --sensitivity
```

### Árbol genealógico
```bash
python3 main.py --mujeres 300 --hombres 300 --años 50 --seed 42 --family-tree
```

### Dashboard interactivo (Streamlit)
```bash
streamlit run app.py
# Abrir http://localhost:8501
```

### Tests
```bash
python3 -m pytest tests/ -v
```

---

## Estructura del proyecto

```
Sim-City/
├── sim/
│   ├── tables.py        # Tablas de probabilidad del enunciado
│   ├── random_vars.py   # Generadores de variables aleatorias (U, Bernoulli, Exp, CDF)
│   ├── person.py        # Entidad Persona (edad, sexo, pareja, hijos, parentesco)
│   ├── couple.py        # Entidad Pareja
│   ├── simulator.py     # Motor de simulación — bucle mensual de 7 pasos
│   ├── calendar_strong_simulator.py  # Motor FEL fuerte (next-event por entidad)
│   ├── factory.py       # Selector/fábrica de motor (step/calendar_strong)
│   ├── monte_carlo.py   # Runner de N corridas con agregación estadística
│   ├── sensitivity.py   # Análisis de sensibilidad (tamaño inicial, distribución de edades)
│   └── genealogy.py     # Árbol genealógico con networkx
├── tests/
│   ├── test_tables.py
│   ├── test_random_vars.py
│   └── test_simulator.py
├── informe/
│   ├── informe.tex      # Informe en formato LNCS
│   └── figures/         # Figuras generadas por los experimentos
├── app.py               # Dashboard Streamlit (3 pestañas)
├── main.py              # CLI principal
├── visualize.py         # Gráficas matplotlib
└── requirements.txt
```

---

## Modelo de simulación

| Aspecto | Decisión |
|---|---|
| Unidad de tiempo | Mes |
| Horizonte | 100 años (1 200 pasos) |
| Motor de ejecución | `step` o `calendar_strong` (FEL fuerte) |
| Probabilidades de muerte | Anuales → mensuales: `1-(1-p)^(1/12)` |
| Probabilidades de embarazo | Mensuales directas |
| Ruptura | Prob. anual 0.2 → mensual: `1-(0.8)^(1/12)` |
| Hijos deseados | Distribución empírica normalizada |
| Duración embarazo | 9 meses fijos |
| Emparejamiento | Barajar listas + iterar secuencialmente |
| Soledad post-ruptura | Exponencial con media según edad |

**Orden del bucle mensual:**
1. Envejecer a todos (+1 mes)
2. Evaluar muertes
3. Evaluar rupturas
4. Decrementar soledad
5. Formar parejas
6. Evaluar embarazos
7. Procesar nacimientos

---

## Experimentos principales

| Experimento | Población inicial | Supervivencia 100 años |
|---|---|---|
| E1 | 200 (100M + 100H) | Extinción ~año 25 |
| E2 | 1 000 (500M + 500H) | Extinción ~año 47 |
| E3 | 2 000 (1000M + 1000H) | Extinción ~año 41 |

> La población tiende a decrecer porque la edad inicial U(0,100) coloca ~55% de los
> individuos en rangos de alta mortalidad (45-76: 30-35%, 76+: 65-70%).
> Con distribución U(0,40) la supervivencia mejora significativamente.
