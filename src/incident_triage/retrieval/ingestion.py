from pathlib import Path
from sentence_transformers import SentenceTransformer
from incident_triage.retrieval.chunker import chunk_corpus
from incident_triage.retrieval.vector_store import (
    setup_database,
    clear_documents,
    store_chunks,
)

MODEL_NAME = "all-MiniLM-L6-v2"


def run_ingestion(data_dir: Path, clear_existing: bool = True):
    """
    Full ingestion pipeline:
    1. Setup database schema
    2. Clear existing documents if requested
    3. Chunk all markdown files in data_dir
    4. Embed chunks using sentence-transformers
    5. Store in pgvector
    """
    print("=== Ingestion Pipeline Starting ===")

    print("\n[1/4] Setting up database schema...")
    setup_database()

    if clear_existing:
        print("\n[2/4] Clearing existing documents...")
        clear_documents()
    else:
        print("\n[2/4] Keeping existing documents...")

    print("\n[3/4] Chunking corpus...")
    chunks = chunk_corpus(data_dir)

    if not chunks:
        print("No chunks found. Check that markdown files have frontmatter.")
        return

    print(f"\n[4/4] Embedding {len(chunks)} chunks...")
    model = SentenceTransformer(MODEL_NAME)

    contents = [chunk.content for chunk in chunks]
    embeddings = model.encode(
        contents,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    print("\nStoring chunks in pgvector...")
    store_chunks(chunks, embeddings.tolist())

    print("\n=== Ingestion Complete ===")
    print(f"Total documents ingested: {len(chunks)}")
