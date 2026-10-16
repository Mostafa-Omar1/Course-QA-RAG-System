# 📚 Standard Course Q&A RAG System

A Retrieval-Augmented Generation (RAG) system that answers student questions using course materials in several file formats (PDF, DOCX, CSV, TXT). Answers come only from the retrieved course content, and every answer lists its sources.

## Features

- **End-to-end RAG pipeline:** extract → clean → chunk → embed → store → retrieve → generate
- **Knowledge base for several courses:** each course is a folder, and you can search all courses or filter to one
- **Multiple file types:** PDF (split by page), DOCX (paragraphs and tables), CSV (each row becomes text), TXT
- **Embeddings and vector database:** `all-MiniLM-L6-v2` sentence embeddings (local ONNX) stored in **ChromaDB** with cosine similarity
- **Grounded answers:** Claude is told to answer only from the retrieved excerpts and to cite them as `[1]`, `[2]`
- **Source attribution:** each answer shows the course, file, page/row and similarity score
- **Gradio web app:** a chat UI, a course filter and a tab for uploading new materials

## Architecture

```
data/courses/<Course>/*.pdf|docx|csv|txt
        │  src/loaders.py     extract + clean text (per page / row / document)
        ▼
        │  src/chunking.py    recursive chunking (800 chars, 150 overlap)
        ▼
        │  src/vectorstore.py MiniLM embeddings → ChromaDB (persistent)
        ▼
question ──► retriever (top-k, similarity threshold, optional course filter)
        │  src/rag.py         prompt with numbered excerpts → Claude
        ▼
answer + citations + sources   (app.py — Gradio UI)
```

## Sample courses (`data/courses/`)

| Course | Files |
|---|---|
| Machine Learning Fundamentals | `ml_lectures.pdf`, `ml_syllabus.txt`, `ml_glossary.csv` |
| Python Programming | `python_notes.docx`, `python_course_info.txt`, `python_schedule.csv` |
| Database Systems | `db_lectures.pdf`, `sql_joins_guide.docx`, `db_assessments.csv`, `db_overview.txt` |

To regenerate the samples, run `python scripts/make_sample_data.py`.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env          # then put your ANTHROPIC_API_KEY in .env
```

## Usage

```bash
python ingest.py      # build the vector DB (app.py also does this automatically on first run)
python app.py         # open http://127.0.0.1:7860
```

Without `ANTHROPIC_API_KEY`, the app still runs. It shows the most relevant retrieved excerpt instead of a generated answer.

### Adding your own courses
Create a folder `data/courses/<Course Name>/`, put PDF/DOCX/CSV/TXT files in it, and run `python ingest.py`. You can also use the **Add materials** tab in the app.

## Example questions
- What is the difference between L1 and L2 regularization?
- What is the late submission policy for the ML course?
- What does `**kwargs` do in Python?
- Explain the ACID properties.
- How much is the midterm worth in Database Systems?

## Tech stack
Python · ChromaDB · Sentence embeddings (all-MiniLM-L6-v2) · Anthropic Claude · Gradio · pypdf · python-docx · pandas
