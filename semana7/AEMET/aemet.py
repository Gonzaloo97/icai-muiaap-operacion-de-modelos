"""Busca la estación solicitada y descarga sus datos de octubre de 2019."""

import json
import os
from pathlib import Path

import requests

BASE_URL = "https://opendata.aemet.es/opendata/api"
ESTACION = "MADRID, CIUDAD UNIVERSITARIA"


def descargar_datos(ruta, api_key):
    """AEMET responde con un enlace: hay que hacer un segundo GET para los datos."""
    respuesta = requests.get(
        BASE_URL + ruta,
        params={"api_key": api_key},
        timeout=30,
    )
    respuesta.raise_for_status()
    informacion = respuesta.json()
    if informacion.get("estado") != 200:
        raise ValueError(
            f"AEMET no devuelve datos: estado {informacion.get('estado')}."
        )

    enlace = informacion.get("datos")
    if not isinstance(enlace, str) or not enlace:
        raise ValueError("AEMET no ha devuelto el enlace a los datos.")

    # La clave solo se envía a la API, no al enlace de descarga.
    respuesta_datos = requests.get(enlace, timeout=30)
    respuesta_datos.raise_for_status()
    datos = respuesta_datos.json()
    if not isinstance(datos, list):
        raise TypeError("Se esperaba una lista de datos de AEMET.")
    return datos


def buscar_estacion(estaciones):
    """Busca por nombre, sin inventar ni fijar de antemano el indicativo."""
    for estacion in estaciones:
        if estacion.get("nombre", "").strip().upper() == ESTACION:
            return estacion["indicativo"]
    raise ValueError(f"No se ha encontrado la estación {ESTACION}.")


def main():
    api_key = os.environ.get("AEMET_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Primero configura la variable de entorno AEMET_API_KEY.")

    try:
        estaciones = descargar_datos(
            "/valores/climatologicos/inventarioestaciones/todasestaciones", api_key
        )
        indicativo = buscar_estacion(estaciones)
        ruta = (
            "/valores/climatologicos/diarios/datos"
            "/fechaini/2019-10-01T00:00:00UTC"
            "/fechafin/2019-10-31T23:59:59UTC"
            f"/estacion/{indicativo}"
        )
        datos = descargar_datos(ruta, api_key)
        if not datos:
            raise ValueError("AEMET ha devuelto una lista vacía para ese periodo.")
    except requests.RequestException:
        # No imprimimos la excepción: su URL podría contener la API key.
        raise SystemExit(
            "No se pudo consultar AEMET. Revisa la conexión y la clave."
        ) from None
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise SystemExit(f"No se han podido obtener los datos: {error}") from None

    archivo = Path(__file__).with_name("datos_octubre_2019.json")
    archivo.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Estación: {ESTACION}. Indicativo: {indicativo}.")
    print(f"Registros descargados: {len(datos)}. Archivo: {archivo.name}")


if __name__ == "__main__":
    main()
