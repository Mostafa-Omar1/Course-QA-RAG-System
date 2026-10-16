"""Retriever + LLM: answer questions using only retrieved course chunks, with source attribution."""
import os

import anthropic

from .vectorstore import VectorStore

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
MIN_SCORE = 0.25   # chunks below this cosine similarity are treated as irrelevant

SYSTEM_PROMPT = """You are a teaching assistant answering student questions about their courses.

Answer ONLY from the numbered course excerpts provided in the user's message. If the excerpts do not
contain the answer, reply exactly: "I couldn't find this in the course materials." Do not use outside
knowledge. Cite the excerpts you used inline with their numbers, like [1] or [2][3]. Keep answers clear
and concise, and answer in the same language as the question."""


def format_source(meta: dict) -> str:
    return f"{meta['course']} / {meta['source']} ({meta['location']})"


def build_context(hits: list[dict]) -> str:
    return "\n\n".join(f"[{i}] Source: {format_source(h['metadata'])}\n{h['text']}"
                       for i, h in enumerate(hits, start=1))


class RAGPipeline:
    def __init__(self, store: VectorStore, k: int = 4):
        self.store = store
        self.k = k
        self.client = anthropic.Anthropic() if os.getenv("ANTHROPIC_API_KEY") else None

    def retrieve(self, question: str, course: str | None = None) -> list[dict]:
        hits = self.store.search(question, k=self.k, course=course)
        return [h for h in hits if h["score"] >= MIN_SCORE]

    def generate(self, question: str, hits: list[dict]) -> str:
        if not hits:
            return "I couldn't find this in the course materials."
        if self.client is None:
            # No API key: return the best-matching excerpt so the app still works offline.
            return ("*(LLM disabled: set ANTHROPIC_API_KEY to get generated answers. "
                    "Most relevant excerpt below.)*\n\n" + hits[0]["text"] + " [1]")

        response = self.client.beta.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{
                "role": "user",
                "content": f"Course excerpts:\n\n{build_context(hits)}\n\nQuestion: {question}",
            }],
        )
        if response.stop_reason == "refusal":
            return "The model declined to answer this question."
        return "".join(b.text for b in response.content if b.type == "text").strip()

    def answer(self, question: str, course: str | None = None) -> dict:
        hits = self.retrieve(question, course)
        return {"answer": self.generate(question, hits), "sources": hits}
