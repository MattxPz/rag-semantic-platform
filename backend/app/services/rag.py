import json
from collections.abc import Generator

from ollama import Client

from app.core.config import settings
from app.models.chunk import Chunk
from app.models.message import Message

_client = Client(host=settings.ollama_base_url)

_SYSTEM_PROMPT = """You are a precise technical document assistant.
Your ONLY source of knowledge for this conversation is the context provided below.

Rules you must follow without exception:
1. Answer exclusively based on the context. Do not use outside knowledge.
2. If the answer is not contained in the context, respond exactly:
   "I could not find information about that in the provided documents."
3. When you reference a specific fact, cite its page number in parentheses,
   e.g. "(page 4)".
4. Be concise and technically accurate.
5. Use the conversation history to resolve references like "it", "that",
   "the one you mentioned", or "explain it further" — they refer to
   whatever was discussed in the previous turns.

--- CONTEXT START ---
{context}
--- CONTEXT END ---"""

# How many previous turns (user+assistant pairs) to include for context.
HISTORY_TURNS = 3


def _build_context(chunks: list[Chunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[Excerpt {i} — Page {chunk.page_number}]\n{chunk.content}")
    return "\n\n---\n\n".join(parts)


def build_search_query(question: str, history: list[Message]) -> str:
    """
    Builds the text used to generate the embedding for retrieval.
    A bare follow-up like "explain it further" carries no retrievable
    meaning on its own, so we fold in the last exchange to give the
    embedding something concrete to match against.
    """
    if not history:
        return question

    last_user = next((m.content for m in reversed(history) if m.role == "user"), None)
    last_assistant = next((m.content for m in reversed(history) if m.role == "assistant"), None)

    parts = []
    if last_user:
        parts.append(f"Previous question: {last_user}")
    if last_assistant:
        # Keep it short — we only need enough to disambiguate the follow-up,
        # not the full answer.
        parts.append(f"Previous answer: {last_assistant[:300]}")
    parts.append(f"Current question: {question}")
    return "\n".join(parts)


def _build_chat_messages(question: str, history: list[Message], context: str) -> list[dict]:
    """Builds the full message list sent to Ollama: system + recent turns + current question."""
    messages = [{"role": "system", "content": _SYSTEM_PROMPT.format(context=context)}]

    recent_history = history[-(HISTORY_TURNS * 2):]
    for message in recent_history:
        messages.append({"role": message.role, "content": message.content})

    messages.append({"role": "user", "content": question})
    return messages


def stream_rag_response(
    question: str,
    chunks: list[Chunk],
    history: list[Message],
) -> Generator[str, None, None]:
    """
    Yields Server-Sent Events (SSE) strings in this order:
      1. One 'sources' event with metadata of the retrieved chunks.
      2. N 'token' events, one per LLM output token.
      3. One 'done' event to signal end of stream.
    On error, yields one 'error' event and stops.
    """
    sources_payload = [
        {
            "chunk_id": str(chunk.id),
            "page_number": chunk.page_number,
            "content_preview": chunk.content[:150],
            "bbox": chunk.bbox,
        }
        for chunk in chunks
    ]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources_payload})}\n\n"

    context = _build_context(chunks)
    messages = _build_chat_messages(question, history, context)

    try:
        stream = _client.chat(
            model=settings.llm_model,
            messages=messages,
            stream=True,
        )

        for chunk_response in stream:
            token = chunk_response.message.content or ""
            if token:
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"
        return

    yield f"data: {json.dumps({'type': 'done'})}\n\n"