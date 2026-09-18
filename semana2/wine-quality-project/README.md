# wine-quality

Proyecto reproducible del caso Wine (S1) empaquetado con `uv`. Entrena un
`ExtraTreesClassifier` sobre `WineQT.csv` para clasificar la calidad del vino
y valida el resultado con un test automático.

## Instalación

Requiere [`uv`](https://docs.astral.sh/uv/) y Python 3.11+.

\`\`\`bash
git clone <https://github.com/Gonzaloo97/icai-muiaap-operacion-de-modelos.git>
cd icai-muiaap-operacion-de-modelos/semana2/wine-quality-project
uv sync --locked
\`\`\`

`uv sync --locked` instala exactamente las versiones fijadas en `uv.lock`,
sin resolver dependencias nuevas.

## Estructura

\`\`\`
wine-quality-project/
├── data/raw/WineQT.csv         # dataset original, sin transformar
├── src/wine_quality/train.py   # entrenamiento y evaluación (módulo del paquete)
├── tests/test_train.py         # test del pipeline de entrenamiento
├── pyproject.toml              # dependencias de ejecución y de desarrollo (dev)
└── uv.lock                     # versiones bloqueadas
\`\`\`

## Comprobaciones

Ejecutar siempre con `--frozen` para no modificar el lock:

\`\`\`bash
uv run --frozen python -m wine_quality.train
uv run --frozen pytest
uv run --frozen ruff check .
\`\`\`