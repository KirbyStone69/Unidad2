# N-reinas

Demo gráfica de N-reinas, separada de la migración de algoritmos evolutivos. Se conservan el código, las imágenes de referencia y sus pruebas.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-reinas.txt
.venv/bin/python reinas.py
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```
