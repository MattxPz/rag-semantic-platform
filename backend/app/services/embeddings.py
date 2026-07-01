from ollama import Client

from app.core.config import settings

# Cliente inicializado una sola vez al cargar el módulo
_client = Client(host=settings.ollama_base_url)


def generate_embedding(text: str) -> list[float]:
    """
    Calls the local Ollama server to generate an embedding vector.
    Returns a list of 768 floats (nomic-embed-text output dimensions).
    """
    response = _client.embed(model=settings.embedding_model, input=text)
    return response.embeddings[0]
