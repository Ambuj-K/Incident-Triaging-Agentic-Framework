from sentence_transformers import SentenceTransformer
from incident_triage.retrieval.vector_store import search_similar
from incident_triage.retrieval.hybrid_search import hybrid_search

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

SYSTEM_TO_METADATA = {
    "inventory_management_system": {
        "team": "platform_engineering",
        "incident_family": "data_pipeline",
    },
    "warehouse_management_system": {
        "team": "platform_engineering",
        "incident_family": "data_pipeline",
    },
    "replenishment_system": {
        "team": "platform_engineering",
        "incident_family": "data_pipeline",
    },
    "etl_pipeline": {
        "team": "platform_engineering",
        "incident_family": "data_pipeline",
    },
    "data_warehouse": {
        "team": "platform_engineering",
        "incident_family": "data_pipeline",
    },
    "pos_systems": {
        "team": "platform_engineering",
        "incident_family": "data_pipeline",
    },
    "purchase_order_system": {
        "team": "platform_engineering",
        "incident_family": "supply_side",
    },
    "commodity_price_feed": {
        "team": "commodity_team",
        "incident_family": "supply_side",
    },
    "supplier_integration_api": {
        "team": "commodity_team",
        "incident_family": "supply_side",
    },
    "futures_contract_feed": {
        "team": "commodity_team",
        "incident_family": "supply_side",
    },
    "procurement_model": {
        "team": "commodity_team",
        "incident_family": "supply_side",
    },
    "ml_forecasting_system": {
        "team": "demand_forecast_team",
        "incident_family": "demand_side",
    },
    "forecast_pipeline": {
        "team": "demand_forecast_team",
        "incident_family": "demand_side",
    },
    "promotional_planning_system": {
        "team": "demand_forecast_team",
        "incident_family": "demand_side",
    },
}


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def infer_metadata_filters(affected_systems: list[str]) -> dict:
    """
    Infer team and incident_family from affected systems list.
    Returns most common team and incident_family across all
    affected systems. Falls back to None if no match found.
    """
    if not affected_systems:
        return {"team": None, "incident_family": None}

    teams = []
    families = []

    for system in affected_systems:
        system_key = (
            system.lower()
            .replace(" ", "_")
            .replace("-", "_")
        )
        if system_key in SYSTEM_TO_METADATA:
            meta = SYSTEM_TO_METADATA[system_key]
            teams.append(meta["team"])
            families.append(meta["incident_family"])

    if not teams:
        return {"team": None, "incident_family": None}

    team = max(set(teams), key=teams.count)
    incident_family = max(set(families), key=families.count)

    return {"team": team, "incident_family": incident_family}


def retrieve(
    query: str,
    top_k: int = 5,
    team: str = None,
    doc_type: str = None,
    incident_family: str = None,
    use_hybrid: bool = True,
) -> list[dict]:
    """
    Retrieve most relevant chunks for a given query.
    Uses hybrid search by default. Falls back to vector only
    if hybrid is disabled.
    """
    if use_hybrid:
        return hybrid_search(
            query=query,
            doc_type=doc_type,
            team=team,
            incident_family=incident_family,
            top_k=top_k,
        )

    model = get_model()
    query_embedding = model.encode(
        query, convert_to_numpy=True
    ).tolist()

    return search_similar(
        query_embedding=query_embedding,
        top_k=top_k,
        team=team,
        doc_type=doc_type,
        incident_family=incident_family,
    )


def retrieve_for_incident(
    incident_description: str,
    top_k: int = 5,
    affected_systems: list[str] = None,
    use_hybrid: bool = True,
) -> dict:
    """
    Retrieve relevant context for an incident.
    Uses affected_systems to infer metadata filters when available.
    Falls back to unfiltered search when systems are unknown.

    Args:
        incident_description: Natural language incident description
        top_k: Number of results to return per corpus type
        affected_systems: List of affected system names from IncidentReport
        use_hybrid: Whether to use hybrid search (default True)
    """
    filters = {}
    if affected_systems:
        filters = infer_metadata_filters(affected_systems)

    runbooks = retrieve(
        query=incident_description,
        top_k=top_k,
        doc_type="runbook",
        team=filters.get("team"),
        incident_family=filters.get("incident_family"),
        use_hybrid=use_hybrid,
    )

    past_incidents = retrieve(
        query=incident_description,
        top_k=top_k,
        doc_type="incident_report",
        team=filters.get("team"),
        incident_family=filters.get("incident_family"),
        use_hybrid=use_hybrid,
    )

    return {
        "runbooks": runbooks,
        "past_incidents": past_incidents,
        "filters_applied": filters,
    }
