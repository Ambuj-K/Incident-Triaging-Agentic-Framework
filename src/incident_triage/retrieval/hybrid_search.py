import os
import math
import numpy as np
from collections import defaultdict
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import psycopg2
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_connection():
    import time
    last_error = None
    delay = 2
    for attempt in range(3):
        try:
            conn = psycopg2.connect(
                os.environ["DATABASE_URL"],
                sslmode="require",
                connect_timeout=10,
            )
            return conn
        except psycopg2.OperationalError as e:
            last_error = e
            if attempt < 2:
                time.sleep(delay)
                delay *= 2
    raise last_error


def vector_search(
    query_embedding: list[float],
    doc_type: str = None,
    team: str = None,
    incident_family: str = None,
    top_k: int = 20,
) -> list[dict]:
    """Vector similarity search with optional metadata filters."""
    conn = get_connection()
    register_vector(conn)
    cursor = conn.cursor()

    filters = []
    params = []

    if doc_type:
        filters.append("doc_type = %s")
        params.append(doc_type)
    if team:
        filters.append("team = %s")
        params.append(team)
    if incident_family:
        filters.append("incident_family = %s")
        params.append(incident_family)

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

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
    all_params = [embedding_array] + params + [embedding_array, top_k]
    cursor.execute(query, all_params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "doc_id": row[0],
            "doc_type": row[1],
            "team": row[2],
            "incident_family": row[3],
            "section": row[4],
            "content": row[5],
            "source_file": row[6],
            "similarity": float(row[7]),
        }
        for row in rows
    ]


def keyword_search(
    query: str,
    doc_type: str = None,
    team: str = None,
    incident_family: str = None,
    top_k: int = 20,
) -> list[dict]:
    """
    BM25-style keyword search using PostgreSQL full text search.
    Handles exact term matching for acronyms and technical terms.
    """
    conn = get_connection()
    cursor = conn.cursor()

    filters = []
    params = []

    if doc_type:
        filters.append("doc_type = %s")
        params.append(doc_type)
    if team:
        filters.append("team = %s")
        params.append(team)
    if incident_family:
        filters.append("incident_family = %s")
        params.append(incident_family)

    # Convert query to tsquery — handle special characters
    # Replace non-alphanumeric with spaces, split into terms
    import re
    terms = re.findall(r'\w+', query.lower())
    if not terms:
        conn.close()
        return []

    # Use plainto_tsquery for robust parsing
    ts_query = " & ".join(terms)

    filter_clause = ""
    if filters:
        filter_clause = "AND " + " AND ".join(filters)

    sql = f"""
        SELECT
            doc_id, doc_type, team, incident_family,
            section, content, source_file,
            ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) as rank
        FROM document_chunks
        WHERE to_tsvector('english', content) @@ plainto_tsquery('english', %s)
        {filter_clause}
        ORDER BY rank DESC
        LIMIT %s;
    """

    all_params = [query, query] + params + [top_k]
    cursor.execute(sql, all_params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "doc_id": row[0],
            "doc_type": row[1],
            "team": row[2],
            "incident_family": row[3],
            "section": row[4],
            "content": row[5],
            "source_file": row[6],
            "keyword_rank": float(row[7]),
        }
        for row in rows
    ]


def reciprocal_rank_fusion(
    vector_results: list[dict],
    keyword_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """
    Combine vector and keyword results using Reciprocal Rank Fusion.
    RRF score = 1/(k + rank) summed across both result lists.
    k=60 is the standard value from the original RRF paper.
    """
    scores = defaultdict(float)
    doc_data = {}

    for rank, result in enumerate(vector_results):
        doc_id = result["doc_id"]
        scores[doc_id] += 1.0 / (k + rank + 1)
        if doc_id not in doc_data:
            doc_data[doc_id] = result

    for rank, result in enumerate(keyword_results):
        doc_id = result["doc_id"]
        scores[doc_id] += 1.0 / (k + rank + 1)
        if doc_id not in doc_data:
            doc_data[doc_id] = result

    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for doc_id, rrf_score in sorted_docs:
        doc = doc_data[doc_id].copy()
        doc["rrf_score"] = rrf_score
        results.append(doc)

    return results


def hybrid_search(
    query: str,
    doc_type: str = None,
    team: str = None,
    incident_family: str = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Full hybrid search combining vector similarity and keyword search
    via Reciprocal Rank Fusion. Returns deduplicated top_k results.
    """
    model = get_model()
    query_embedding = model.encode(query, convert_to_numpy=True).tolist()

    vec_results = vector_search(
        query_embedding=query_embedding,
        doc_type=doc_type,
        team=team,
        incident_family=incident_family,
        top_k=top_k * 3,
    )

    kw_results = keyword_search(
        query=query,
        doc_type=doc_type,
        team=team,
        incident_family=incident_family,
        top_k=top_k * 3,
    )

    fused = reciprocal_rank_fusion(vec_results, kw_results)

    # Deduplicate by doc_id
    seen = set()
    deduped = []
    for result in fused:
        if result["doc_id"] not in seen:
            seen.add(result["doc_id"])
            deduped.append(result)

    return deduped[:top_k]


def hybrid_retrieve_for_incident(
    incident_description: str,
    top_k: int = 5,
) -> dict:
    """
    Retrieve relevant context using hybrid search.
    Returns runbooks and past incidents separately.
    """
    runbooks = hybrid_search(
        query=incident_description,
        doc_type="runbook",
        top_k=top_k,
    )

    past_incidents = hybrid_search(
        query=incident_description,
        doc_type="incident_report",
        top_k=top_k,
    )

    return {
        "runbooks": runbooks,
        "past_incidents": past_incidents,
    }
