"""ChromaDB vector store with sentence-embedding (all-MiniLM-L6-v2, ONNX) retrieval."""
from pathlib import Path
import hashlib

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

COLLECTION = "course_materials"


class VectorStore:
    def __init__(self, persist_dir: str | Path):
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.embed = DefaultEmbeddingFunction()   # all-MiniLM-L6-v2, runs locally
        self.collection = self.client.get_or_create_collection(
            COLLECTION, embedding_function=self.embed, metadata={"hnsw:space": "cosine"}
        )

    def reset(self):
        self.client.delete_collection(COLLECTION)
        self.collection = self.client.get_or_create_collection(
            COLLECTION, embedding_function=self.embed, metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: list[dict], batch_size: int = 64):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            ids = [
                hashlib.md5(f"{c['metadata']['course']}|{c['metadata']['source']}|"
                            f"{c['metadata']['location']}|{c['metadata']['chunk']}".encode()).hexdigest()
                for c in batch
            ]
            self.collection.upsert(
                ids=ids,
                documents=[c["text"] for c in batch],
                metadatas=[c["metadata"] for c in batch],
            )

    def count(self) -> int:
        return self.collection.count()

    def courses(self) -> list[str]:
        metas = self.collection.get(include=["metadatas"])["metadatas"]
        return sorted({m["course"] for m in metas})

    def search(self, query: str, k: int = 4, course: str | None = None) -> list[dict]:
        where = {"course": course} if course else None
        res = self.collection.query(query_texts=[query], n_results=k, where=where)
        return [
            {"text": doc, "metadata": meta, "score": round(1 - dist, 3)}
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
        ]
