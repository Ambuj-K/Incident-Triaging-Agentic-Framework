from sentence_transformers import SentenceTransformer
from incident_triage.retrieval.vector_store import search_similar

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model() -> SentenceTransformer:
    """Lazy load model — only instantiate once."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def retrieve(
    query: str,
    top_k: int = 5,
    team: str = None,
    doc_type: str = None,
    incident_family: str = None,
) -> list[dict]:
    """
    Retrieve most relevant chunks for a given query.
    Optional filters narrow retrieval to specific team, doc type, or incident family.
    """
    model = get_model()
    query_embedding = model.encode(query, convert_to_numpy=True).tolist()

    results = search_similar(
        query_embedding=query_embedding,
        top_k=top_k,
        team=team,
        doc_type=doc_type,
        incident_family=incident_family,
    )

    return results


def retrieve_for_incident(
    incident_description: str,
    top_k: int = 5,
) -> dict:
    """
    Retrieve relevant context for an incident from all corpus types.
    Returns runbooks, past incidents, and system docs separately.
    """
    runbooks = retrieve(
        query=incident_description,
        top_k=top_k,
        doc_type="runbook",
    )

    past_incidents = retrieve(
        query=incident_description,
        top_k=top_k,
        doc_type="incident_report",
    )

    return {
        "runbooks": runbooks,
        "past_incidents": past_incidents,
    }
