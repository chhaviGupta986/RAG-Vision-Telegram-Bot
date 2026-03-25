import logging
import pickle
from collections import OrderedDict
from pathlib import Path
from typing import Callable, Iterable, Optional

import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

INDEX_PATH = Path("db/faiss.index")
META_PATH = Path("db/metadata.pkl")
CACHE_PATH = Path("db/query_cache.pkl")
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MAX_PROMPT_CHARS = 3600
MAX_DISTANCE_THRESHOLD = 1.2
CACHE_SIZE = 100
MAX_ANSWER_WORDS = 80

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index(str(INDEX_PATH))
with META_PATH.open("rb") as f:
    metadata = pickle.load(f)


class RagError(Exception):
    pass


class NoRelevantContextError(RagError):
    pass


class OllamaError(RagError):
    pass


class SummarizationError(RagError):
    pass


def _truncate_context(context: str) -> str:
    if len(context) <= MAX_PROMPT_CHARS:
        return context
    return context[-MAX_PROMPT_CHARS:]


def _mean_distance(distances: Iterable[float]) -> float:
    return float(np.mean(distances))


def _has_relevant_context(distances: Iterable[float]) -> bool:
    mean = _mean_distance(distances)
    logger.debug("FAISS distances: %s (mean=%s)", list(distances)[:3], mean)
    if mean <= MAX_DISTANCE_THRESHOLD:
        return True
    best = min(distances)
    logger.debug("Best distance=%s", best)
    return best <= MAX_DISTANCE_THRESHOLD * 1.1


def _format_source_line(index: int, chunk: str, idx: int) -> str:
    snippet = chunk.strip().replace("\n", " ")
    limit = 100
    if len(snippet) <= limit:
        preview = snippet
        indicator = ""
    else:
        truncated = snippet[:limit]
        last_space = truncated.rfind(" ")
        if last_space > limit * 0.7:
            preview = truncated[:last_space]
        else:
            preview = truncated
        indicator = "..."
    return f"📚 Source {idx + 1}: \"{preview}{indicator}\""


def _call_ollama(messages: list[dict]) -> str:
    # payload = {"model": "smollm:135m", "messages": messages, "stream": False}
    payload = {"model": "phi3:mini", "messages": messages, "stream": False}
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Ollama request failed: %s", exc)
        raise OllamaError("Ollama serve request failed") from exc

    data = response.json()
    choices = data.get("choices") or []

    message = None
    if choices:
        message = choices[0].get("message", {})
    else:
        message = data.get("message")
        if not message:
            logger.error(
                "Ollama serve returned no message payload: status=%s data=%s",
                response.status_code,
                data,
            )
            raise OllamaError("Ollama serve returned an empty response")
    content = message.get("content", "")
    if isinstance(content, list):
        answer = "".join(part.get("text", "") for part in content).strip()
    else:
        answer = content.strip()

    if not answer:
        raise OllamaError("Ollama returned an empty answer")
    return answer


QUERY_CACHE: "OrderedDict[str, tuple[str, list[str]]]" = OrderedDict()


def _load_query_cache() -> None:
    if not CACHE_PATH.exists():
        return
    try:
        with CACHE_PATH.open("rb") as fh:
            cached_entries = pickle.load(fh)
        if isinstance(cached_entries, OrderedDict):
            QUERY_CACHE.update(cached_entries)
        elif isinstance(cached_entries, list):
            QUERY_CACHE.update(cached_entries)
        while len(QUERY_CACHE) > CACHE_SIZE:
            QUERY_CACHE.popitem(last=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load query cache from %s: %s", CACHE_PATH, exc)


def _persist_query_cache() -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_PATH.open("wb") as fh:
            pickle.dump(list(QUERY_CACHE.items()), fh)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist query cache to %s: %s", CACHE_PATH, exc)


def _normalize_query(query: str) -> str:
    return " ".join(query.lower().strip().split())


_load_query_cache()


def answer_query(
    query: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    conversation_history: Optional[list[str]] = None,
) -> tuple[str, list[str]]:

    normalized = _normalize_query(query)
    if conversation_history is None and normalized in QUERY_CACHE:
        return QUERY_CACHE[normalized]
    emb = model.encode([query])
    distances, indices = index.search(np.array(emb), k=3)

    if not _has_relevant_context(distances[0]):
        raise NoRelevantContextError("No relevant chunks found for the query")

    context_entries = [metadata[i]["chunk"] for i in indices[0]]
    context = _truncate_context("\n".join(context_entries))
    logger.debug("Context length %s chars", len(context))

    if progress_callback:
        progress_callback("Relevant documents retrieved. Generating the answer…")

    system_prompt = (
        "You are a concise, factual assistant that answers questions *only* using the provided context. "
        "If the context does not contain the answer, reply with: "
        "'The context does not provide this information.' "
        "If the user says something unrelated to the context (e.g., greetings like 'Hi' or 'Bye'), respond politely in a short and friendly manner."
    )
    history_prompt = ""
    if conversation_history:
        history_text = "\n".join(
            f"{idx + 1}. {entry}" for idx, entry in enumerate(conversation_history)
        )
        history_prompt = f"\nConversation history (most recent first):\n{history_text}"

    user_prompt = (
        "Context:\n"
        f"{context}\n\n"
        f"Question: {query}\n"
        f"Provide a concise response within {MAX_ANSWER_WORDS} words."
        f"{history_prompt}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    answer = _call_ollama(messages)
    source_lines = []
    if not answer.lower().startswith("the context does not provide"):
        for idx, i in enumerate(indices[0]):
            source_lines.append(_format_source_line(i, metadata[i]["chunk"], idx))
    if conversation_history is None:
        QUERY_CACHE[normalized] = (answer, source_lines)
        while len(QUERY_CACHE) > CACHE_SIZE:
            QUERY_CACHE.popitem(last=False)
        _persist_query_cache()
    return answer, source_lines


def summarize_text(text: str) -> str:
    if not text.strip():
        raise SummarizationError("No text to summarize")

    messages = [
        {
            "role": "system",
            "content": "You summarize passages into 2-3 bullet points. Keep it short and factual.",
        },
        {
            "role": "user",
            "content": (
                "Summarize the following text:\n"
                f"{text}\n"
                "Focus on the core facts and keep it to 2-3 bullet sentences."
            ),
        },
    ]

    answer = _call_ollama(messages)
    return answer
