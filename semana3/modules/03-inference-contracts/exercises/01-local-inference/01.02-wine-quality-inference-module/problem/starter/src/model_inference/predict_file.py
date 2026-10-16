"""Script CLI que encadena contratos, preprocesado e inferencia."""

import argparse
import csv
import sys
from pathlib import Path

from model_inference.contracts import WineQualityPrediction, WineQualityRequest
from model_inference.inference import (
    DEFAULT_MODEL_PATH,
    infer_wine_quality,
    load_wine_quality_model,
)
from model_inference.preprocess import PREPROCESING_VERSION, preprocess_wine_request


def predict_file(input_path, output_path, model_path):
    artifact = load_wine_quality_model(model_path)  # 1. cargamos el modelo
    results = []  # aquí guardamos las predicciones (en memoria)

    with open(input_path, encoding="utf-8") as file:  # 2. abrimos el CSV
        for row in csv.DictReader(file):  # cada fila es un diccionario
            sample_id = row.pop("sample_id")  # sacamos el id; quedan las medidas
            try:
                request = WineQualityRequest(**row)  # 3. validamos la fila
                features = preprocess_wine_request(request)  # 4. vector ordenado
                band, confidence = infer_wine_quality(artifact, features)  # 5.
                prediction = WineQualityPrediction(  # 6. validamos la salida
                    sample_id=sample_id,
                    quality_band=band,
                    confidence=confidence,
                    model_version=artifact["model_version"],
                    preprocessing_version=PREPROCESING_VERSION,
                )
            except ValueError as error:  # si algo falla, decimos en qué fila
                raise ValueError(f"Fila {sample_id}: {error}") from error
            results.append(prediction.model_dump())  # guardamos como diccionario

    # 7. Solo llegamos aquí si TODAS las filas eran válidas: ahora escribimos
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)  # crea .tmp/
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())  # columnas
        writer.writeheader()  # cabecera
        writer.writerows(results)  # todas las filas
    return len(results)  # cuántas predicciones hemos escrito


def main():
    parser = argparse.ArgumentParser()  # lee los argumentos del comando
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH)
    args = parser.parse_args()

    try:
        count = predict_file(args.input, args.output, args.model)
    except (ValueError, FileNotFoundError) as error:  # cualquier fallo...
        print(f"error: {error}", file=sys.stderr)  # ...se muestra por stderr
        return 2  # código 2 = ha fallado
    print(f"Predicciones escritas: {count}")
    return 0  # código 0 = todo bien


if __name__ == "__main__":
    sys.exit(main())