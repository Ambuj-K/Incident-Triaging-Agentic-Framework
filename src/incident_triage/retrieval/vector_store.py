import os
import numpy as np
from pgvector.psycopg2 import register_vector
import psycopg2, time
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from incident_triage.retrieval.chunker import Chunk

load_dotenv()

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 dimension


def get_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require"
    )


def setup_database():
    """Create pgvector extension and documents table if not exists."""
    conn = get_connection()
    register_vector(conn)
    cursor = conn.cursor()

    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            doc_id TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            team TEXT NOT NULL,
            incident_family TEXT NOT NULL,
            section TEXT NOT NULL,
            source_file TEXT NOT NULL,
            systems TEXT[],
            severity_range TEXT[],
            status TEXT,
            related_runbook TEXT,
            content TEXT NOT NULL,
            embedding vector({EMBEDDING_DIM})
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_doc_type 
        ON document_chunks(doc_type);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_team 
        ON document_chunks(team);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incident_family 
        ON document_chunks(incident_family);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_embedding 
        ON document_chunks 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10);
    """)

    conn.commit()
    conn.close()
    print("Database schema ready")


def clear_documents():
    """Clear all documents — use before re-ingesting corpus."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE document_chunks;")
    conn.commit()
    conn.close()
    print("Document table cleared")


def store_chunks(chunks: list[Chunk], embeddings: list[list[float]]):
    """Store chunks with their embeddings in pgvector."""
    conn = get_connection()
    register_vector(conn)
    cursor = conn.cursor()

    records = []
    for chunk, embedding in zip(chunks, embeddings):
        records.append((
            chunk.doc_id,
            chunk.doc_type,
            chunk.team,
            chunk.incident_family,
            chunk.section,
            chunk.source_file,
            chunk.systems,
            chunk.severity_range,
            chunk.status,
            chunk.related_runbook,
            chunk.content,
            np.array(embedding),
        ))

    execute_values(
        cursor,
        """
        INSERT INTO document_chunks 
        (doc_id, doc_type, team, incident_family, section, 
         source_file, systems, severity_range, status, 
         related_runbook, content, embedding)
        VALUES %s
        """,
        records,
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )

    conn.commit()
    conn.close()
    print(f"Stored {len(records)} chunks")


def search_similar(
    query_embedding: list[float],
    top_k: int = 5,
    team: str = None,
    doc_type: str = None,
    incident_family: str = None,
) -> list[dict]:
    """
    Search for similar chunks using cosine similarity.
    Optional metadata filters narrow the search before vector comparison.
    """
    conn = get_connection()
    register_vector(conn)
    cursor = conn.cursor()

    filters = []
    params = []

    if team:
        filters.append("team = %s")
        params.append(team)
    if doc_type:
        filters.append("doc_type = %s")
        params.append(doc_type)
    if incident_family:
        filters.append("incident_family = %s")
        params.append(incident_family)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    query = f"""
        SELECT 
            doc_id, doc_type, team, incident_family,
            section, content, source_file,
            1 - (embedding <=> %s::vector) as similarity
        FROM document_chunks
        {where_clause}
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """

    embedding_array = np.array(query_embedding)
    params = [embedding_array] + params + [embedding_array, top_k]

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "doc_id": row[0],
            "doc_type": row[1],
            "team": row[2],
            "incident_family": row[3],
            "section": row[4],
            "content": row[5],
            "source_file": row[6],
            "similarity": float(row[7]),
        })

    return results

def get_connection(retries: int = 3, delay: int = 2):
    """Get database connection with retry for Neon cold starts."""
    last_error = None
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(
                os.environ["DATABASE_URL"],
                sslmode="require",
                connect_timeout=10,
            )
            return conn
        except psycopg2.OperationalError as e:
            last_error = e
            if attempt < retries - 1:
                print(f"Connection attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
    raise last_error
