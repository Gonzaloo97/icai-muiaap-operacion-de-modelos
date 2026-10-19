"""Transformación de una muestra validada en el vector del modelo."""

# Herramienta de Python que crea el constructor de una clase automáticamente.
from dataclasses import dataclass

# El contrato de entrada: el tipo de dato que recibe nuestra función.
from model_inference.contracts import WineQualityRequest

# Nombre de la versión de este preprocesado. Se escribe en el CSV de salida.
PREPROCESING_VERSION = "wine-red-features-v1"

# Orden en que se entrenó el modelo. Viene dado: no se cambia.
# Es una tupla ( ) para que nadie pueda modificarla por accidente.
FEATURE_NAMES = (
    "fixed_acidity",
    "volatile_acidity",
    "citric_acid",
    "residual_sugar",
    "chlorides",
    "free_sulfur_dioxide",
    "total_sulfur_dioxide",
    "density",
    "ph",
    "sulphates",
    "alcohol",
)


# @dataclass crea solo el constructor: WineFeatures(values=[...]).
@dataclass
class WineFeatures:
    values: list[float]  # la lista de 11 números ya ordenados

    def as_vector(self) -> list[float]:  # método que pide el test
        return self.values  # devuelve la lista guardada dentro del objeto


# Recibe una petición ya validada y devuelve un WineFeatures.
def preprocess_wine_request(request: WineQualityRequest) -> WineFeatures:
    # Recorremos los 11 nombres EN ORDEN y sacamos cada valor de la petición
    values = [getattr(request, name) for name in FEATURE_NAMES]
    return WineFeatures(values=values)  # lo metemos en un WineFeatures
