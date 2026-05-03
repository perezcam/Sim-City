# Compilar el informe

## Requisito: clase llncs

El archivo `informe.tex` usa la clase `llncs` de Springer.
Descárgala desde:
https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines

Coloca `llncs.cls` en esta misma carpeta (`informe/`).

## Instalar LaTeX (Ubuntu/Debian)

```bash
sudo apt install texlive-full
# o mínimo:
sudo apt install texlive-latex-extra texlive-lang-spanish
```

## Compilar

```bash
cd informe/
make          # genera informe.pdf
make clean    # limpia archivos auxiliares
```

O manualmente:
```bash
pdflatex informe.tex
pdflatex informe.tex   # segunda pasada para referencias cruzadas
```

## Añadir gráficas al informe

1. Ejecutar la simulación y exportar las figuras:
   ```bash
   cd ..
   python3 -c "
   from sim.simulator import Simulator
   from visualize import plot_all
   import matplotlib
   matplotlib.use('Agg')
   import matplotlib.pyplot as plt

   sim = Simulator(500, 500, seed=42)
   stats = sim.run()
   plot_all(stats, save_path='informe/figures/resultados.png')
   "
   ```
2. Insertar la imagen en el LaTeX con `\includegraphics`.
