import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


def definir_tool():
    """Describe la herramienta usando el mismo contrato que la API."""
    return {
        "type": "function",
        "function": {
            "name": NOMBRE_TOOL,
            "description": "Calcula el riesgo de impago con los seis datos del préstamo.",
            "parameters": PrestamoEntrada.model_json_schema(),
        },
    }


def ejecutar_tool(nombre, argumentos_json):
    """Devuelve un resultado o un error que el LLM pueda entender y corregir."""
    if nombre != NOMBRE_TOOL:
        return {"ok": False, "error": "Herramienta desconocida."}

    try:
        datos = json.loads(argumentos_json)
    except (json.JSONDecodeError, TypeError):
        return {"ok": False, "error": "Los argumentos no son JSON válido."}

    try:
        entrada = PrestamoEntrada.model_validate(datos)
    except ValidationError as error:
        # Indicamos el campo incorrecto sin repetir los datos personales.
        detalles = []
        for fallo in error.errors():
            campo = ".".join(str(parte) for parte in fallo["loc"])
            detalles.append(f"{campo}: {fallo['msg']}")
        return {"ok": False, "error": "; ".join(detalles)}

    try:
        prediccion = predecir(entrada)
    except Exception:  # noqa: BLE001 - la tool debe devolver un error al LLM
        # La herramienta siempre devuelve un dict, incluso si falla el modelo.
        return {"ok": False, "error": "No se ha podido ejecutar el modelo."}

    return {
        "ok": True,
        "probabilidad_impago": prediccion.probabilidad_impago,
        "decision": prediccion.decision,
    }


def responder(mensajes, llm):
    """Repite pregunta -> herramienta -> resultado hasta obtener una respuesta."""
    historial = [{"role": "system", "content": SISTEMA}]
    for mensaje in mensajes:
        historial.append(mensaje.model_dump())

    herramientas = [definir_tool()]
    ultima_herramienta = None

    for _ in range(MAX_VUELTAS):
        respuesta = llm.completar(historial, herramientas)
        historial.append(respuesta)
        llamadas = respuesta.get("tool_calls")

        # Sin llamadas a herramientas, el LLM ya ha terminado.
        if not llamadas:
            return ChatSalida(
                respuesta=respuesta.get("content") or "No he recibido una respuesta.",
                herramienta=ultima_herramienta,
            )

        for llamada in llamadas:
            funcion = llamada["function"]
            resultado = ejecutar_tool(funcion["name"], funcion["arguments"])
            ultima_herramienta = HerramientaUsada(
                nombre=funcion["name"],
                argumentos=leer_argumentos(funcion["arguments"]),
                resultado=resultado,
            )
            # tool_call_id une este resultado con la llamada que lo pidió.
            historial.append(
                {
                    "role": "tool",
                    "tool_call_id": llamada["id"],
                    "content": json.dumps(resultado, ensure_ascii=False),
                }
            )

    return ChatSalida(
        respuesta="He alcanzado el límite de intentos. Revisa los datos e inténtalo de nuevo.",
        herramienta=ultima_herramienta,
    )
