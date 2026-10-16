"""Gradio web app for the Course Q&A RAG system.

Run:  python app.py   (builds the index automatically on first launch)
"""
from pathlib import Path
import shutil

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from src.chunking import chunk_documents  # noqa: E402
from src.loaders import SUPPORTED, load_courses, load_file  # noqa: E402
from src.rag import RAGPipeline, format_source  # noqa: E402
from src.vectorstore import VectorStore  # noqa: E402

DATA_DIR = Path("data/courses")
ALL = "All courses"

store = VectorStore("chroma_db")
if store.count() == 0:
    store.add_chunks(chunk_documents(load_courses(DATA_DIR)))
rag = RAGPipeline(store)


def course_choices():
    return [ALL] + store.courses()


def ask(question, course, history):
    history = history or []
    if not question.strip():
        return history, "", ""
    result = rag.answer(question, None if course == ALL else course)
    sources = "\n\n".join(
        f"**[{i}] {format_source(h['metadata'])}** — similarity {h['score']}\n\n> {h['text'][:400]}"
        + ("…" if len(h["text"]) > 400 else "")
        for i, h in enumerate(result["sources"], start=1)
    ) or "_No relevant sources found._"
    history += [{"role": "user", "content": question},
                {"role": "assistant", "content": result["answer"]}]
    return history, "", sources


def upload(files, course_name):
    course_name = (course_name or "").strip()
    if not files or not course_name:
        return "Choose files and enter a course name.", gr.update()
    folder = DATA_DIR / course_name
    folder.mkdir(parents=True, exist_ok=True)
    docs = []
    for f in files:
        src = Path(f if isinstance(f, str) else f.name)
        if src.suffix.lower() not in SUPPORTED:
            continue
        dest = folder / src.name
        shutil.copy(src, dest)
        docs.extend(load_file(dest, course_name))
    chunks = chunk_documents(docs)
    store.add_chunks(chunks)
    return f"Added {len(chunks)} chunks to '{course_name}'.", gr.update(choices=course_choices())


with gr.Blocks(title="Course Q&A RAG") as demo:
    gr.Markdown("# 📚 Course Q&A Assistant\nAsk questions about your course materials "
                "(PDF, DOCX, CSV, TXT). Answers are generated only from retrieved content, with sources.")
    with gr.Tab("Ask"):
        with gr.Row():
            with gr.Column(scale=3):
                chat = gr.Chatbot(height=420, label="Conversation")
                with gr.Row():
                    q = gr.Textbox(placeholder="e.g. What is overfitting?", scale=4, show_label=False)
                    btn = gr.Button("Ask", variant="primary", scale=1)
            with gr.Column(scale=2):
                course = gr.Dropdown(course_choices(), value=ALL, label="Course")
                srcs = gr.Markdown(label="Sources")
        gr.Examples(["What is the difference between L1 and L2 regularization?",
                     "What is the late submission policy for the ML course?",
                     "What does **kwargs do in Python?",
                     "Explain the ACID properties.",
                     "How much is the midterm worth in Database Systems?"], inputs=q)
        btn.click(ask, [q, course, chat], [chat, q, srcs])
        q.submit(ask, [q, course, chat], [chat, q, srcs])
    with gr.Tab("Add materials"):
        files = gr.File(file_count="multiple", file_types=[".pdf", ".docx", ".csv", ".txt"])
        new_course = gr.Textbox(label="Course name")
        status = gr.Markdown()
        gr.Button("Index files").click(upload, [files, new_course], [status, course])

if __name__ == "__main__":
    demo.launch()
