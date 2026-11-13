import joblib

from app.config import MODEL_PATH
from app.schemas.prestamo import PrediccionSalida, PrestamoEntrada

# Orden en el que el modelo espera las variables
VARIABLES = [
    "edad",
    "ingresos_mensuales",
    "importe_prestamo",
    "plazo_meses",
    "antiguedad_laboral_anios",
    "impagos_previos",
]

# Se carga al importar este módulo, no cada vez que llega una petición.
modelo = joblib.load(MODEL_PATH)


def decidir(probabilidad):
    """Aplica los tres intervalos indicados en el enunciado."""
    if probabilidad < 0.2:
        return "aprobar"
    if probabilidad < 0.5:
        return "revisar"
    return "rechazar"


def predecir(entrada: PrestamoEntrada) -> PrediccionSalida:
    """Ordena los datos, ejecuta el modelo y valida su respuesta."""
    datos = entrada.model_dump()
    valores = []
    for variable in VARIABLES:
        valores.append(datos[variable])

    # El modelo recibe una tabla: una fila con las seis variables.
    probabilidad = float(modelo.predict_proba([valores])[0][1])
    return PrediccionSalida(
        probabilidad_impago=probabilidad,
        decision=decidir(probabilidad),
    )
