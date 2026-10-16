"""Build the vector database: extract -> clean -> chunk -> embed -> store.

Usage:  python ingest.py [--data data/courses] [--db chroma_db] [--chunk-size 800] [--overlap 150]
"""
import argparse
from collections import Counter
from pathlib import Path

from src.chunking import chunk_documents
from src.loaders import load_courses
from src.vectorstore import VectorStore


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/courses")
    ap.add_argument("--db", default="chroma_db")
    ap.add_argument("--chunk-size", type=int, default=800)
    ap.add_argument("--overlap", type=int, default=150)
    args = ap.parse_args()

    docs = load_courses(Path(args.data))
    chunks = chunk_documents(docs, args.chunk_size, args.overlap)
    print(f"Loaded {len(docs)} documents -> {len(chunks)} chunks")
    for (course, ftype), n in sorted(Counter((c["metadata"]["course"], c["metadata"]["file_type"])
                                             for c in chunks).items()):
        print(f"  {course:32s} {ftype:5s} {n} chunks")

    store = VectorStore(args.db)
    store.reset()
    store.add_chunks(chunks)
    print(f"Stored {store.count()} chunks in '{args.db}'")


if __name__ == "__main__":
    main()
