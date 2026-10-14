"""TODO: transformación de una muestra validada en el vector del modelo."""
# Herramienta de Python que crea el constructor de una clase automáticamente.
from dataclasses import dataclass

# El contrato de entrada: el tipo de dato que recibe nuestra función.
from model_inference.contracts import WineQualityRequest

# Nombre de la versión de este preprocesado. Se escribe en el CSV de salida
PREPROCESING_VERSION = "wine-red-features-v1"

# Orden en que se entrenó el modelo. Viene dado: no se cambia.
# Es una tupla ( ) para que nadie pueda modificarla por accidente.
# Este contrato se entrega ya decidido: no cambies ni los nombres ni el orden.
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

# Implementa WineFeatures y preprocess_wine_request(). El orden anterior debe
# coincidir con el artefacto, no con un orden arbitrario del CSV.

# @dataclass crea solo el constructor: así se puede hacer WineFeatures(values=[...]).
@dataclass
class WineFeatures:
     
    values: list[float]   # El único dato que guarda el objeto: la lista de 11 números ordenados.

    def as_vector(self) -> list[float]: # Método que pide el test. self es el propio objeto.
        return self.values # Devuelve la lista que se guardó dentro del objeto.

# Recibe una petición ya validada y devuelve un WineFeatures.
def preprocess_wine_request(request: WineQualityRequest) -> WineFeatures: 
    #Recorremos los 11 nombres EN ORDEN y los metemos en una lista que llamamos values
    values = [getattr(request, name) for name in FEATURE_NAMES]
    return WineFeatures(values=values) # Metemos la lista ya ordenada dentro de un objeto WineFeatures y lo devolvemos.

