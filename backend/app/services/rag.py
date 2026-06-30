import json
from collections.abc import Generator

from ollama import Client

from app.core.config import settings
from app.models.chunk import Chunk

_client = Client(host=settings.ollama_base_url)

# ── System prompt ────────────────────────────────────────────────────────────
# Explicit rules force the model to stay inside the retrieved context
# and avoid hallucinating facts that aren't in the documents.
_SYSTEM_PROMPT = """You are a precise technical document assistant.
Your ONLY source of knowledge for this conversation is the context provided below.

Rules you must follow without exception:
1. Answer exclusively based on the context. Do not use outside knowledge.
2. If the answer is not contained in the context, respond exactly:
   "I could not find information about that in the provided documents."
3. When you reference a specific fact, cite its page number in parentheses,
   e.g. "(page 4)".
4. Be concise and technically accurate.

--- CONTEXT START ---
{context}
--- CONTEXT END ---"""


def _build_context(chunks: list[Chunk]) -> str:
    """Formats retrieved chunks into a numbered context block."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[Excerpt {i} — Page {chunk.page_number}]\n{chunk.content}")
    return "\n\n---\n\n".join(parts)


def stream_rag_response(
    question: str,
    chunks: list[Chunk],
) -> Generator[str, None, None]:
    """
    Yields Server-Sent Events (SSE) strings in this order:
      1. One 'sources' event with metadata of the retrieved chunks.
      2. N 'token' events, one per LLM output token.
      3. One 'done' event to signal end of stream.
    On error, yields one 'error' event and stops.
    """
    # ── Event 1: sources ─────────────────────────────────────────────────────
    sources_payload = [
        {
            "chunk_id": str(chunk.id),
            "page_number": chunk.page_number,
            "content_preview": chunk.content[:150],
        }
        for chunk in chunks
    ]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources_payload})}\n\n"

    # ── Build prompt ──────────────────────────────────────────────────────────
    context = _build_context(chunks)
    system = _SYSTEM_PROMPT.format(context=context)

    try:
        stream = _client.chat(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            stream=True,
        )

        # ── Events 2…N: tokens ───────────────────────────────────────────────
        for chunk_response in stream:
            token = chunk_response.message.content or ""
            if token:
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"
        return

    # ── Final event: done ─────────────────────────────────────────────────────
    yield f"data: {json.dumps({'type': 'done'})}\n\n"