"""Split documents into overlapping chunks, preferring paragraph and sentence boundaries."""
import re

SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split(text: str, size: int, seps: list[str]) -> list[str]:
    if len(text) <= size:
        return [text]
    if not seps:
        return [text[i:i + size] for i in range(0, len(text), size)]
    sep, rest = seps[0], seps[1:]
    pieces = [p for p in text.split(sep) if p.strip()]
    if len(pieces) == 1:
        return _split(text, size, rest)
    out = []
    for p in pieces:
        p = p if sep != ". " else p.rstrip(".") + "."
        out.extend(_split(p, size, rest) if len(p) > size else [p])
    return out


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Greedily pack small pieces into chunks up to `chunk_size`, carrying `overlap` chars forward."""
    pieces = _split(text, chunk_size, SEPARATORS)
    chunks, current = [], ""
    for piece in pieces:
        candidate = f"{current}\n{piece}".strip() if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        chunks.append(current)
        tail = current[-overlap:] if overlap else ""
        tail = tail[tail.find(" ") + 1:] if " " in tail else tail   # don't start mid-word
        current = f"{tail} {piece}".strip()
    if current:
        chunks.append(current)
    return [re.sub(r"[ \t]+", " ", c).strip() for c in chunks if c.strip()]


def chunk_documents(docs: list[dict], chunk_size: int = 800, overlap: int = 150) -> list[dict]:
    chunks = []
    for doc in docs:
        for i, text in enumerate(chunk_text(doc["text"], chunk_size, overlap)):
            chunks.append({"text": text, "metadata": {**doc["metadata"], "chunk": i}})
    return chunks
