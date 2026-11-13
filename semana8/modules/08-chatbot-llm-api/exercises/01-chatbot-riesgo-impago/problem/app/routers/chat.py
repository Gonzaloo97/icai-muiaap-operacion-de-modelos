from fastapi import APIRouter, Depends

from app.schemas.chat import ChatEntrada, ChatSalida
from app.services.llm import get_llm
from app.services.orquestador import responder

router = APIRouter()


@router.post("/chat", response_model=ChatSalida)
def chat(entrada: ChatEntrada, llm=Depends(get_llm)):  # noqa: B008 - dependencia de FastAPI
    """Pasa la conversación al orquestador y devuelve la respuesta del chat."""
    return responder(entrada.mensajes, llm)
