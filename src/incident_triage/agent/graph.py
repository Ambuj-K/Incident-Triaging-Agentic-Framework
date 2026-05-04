from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from incident_triage.agent.state import AgentState
from incident_triage.agent.nodes import (
    validate_input,
    request_clarification,
    classify_incident,
    retrieve_context,
    investigate_with_context,
    human_review,
    auto_resolve,
)
from incident_triage.agent.edges import (
    route_after_validation,
    route_after_classification,
    route_after_investigation,
)

def build_graph(interrupt_on_human_review: bool = True):
    """
    Build and compile the incident triage agent graph.

    Args:
        interrupt_on_human_review: If True, graph pauses at human_review
            node and waits for human input before continuing.
            Set False for automated testing.
    """
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("validate_input", validate_input)
    builder.add_node("request_clarification", request_clarification)
    builder.add_node("classify_incident", classify_incident)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("investigate_with_context", investigate_with_context)
    builder.add_node("human_review", human_review)
    builder.add_node("auto_resolve", auto_resolve)

    # Set entry point
    builder.set_entry_point("validate_input")

    # Add conditional edges
    builder.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "request_clarification": "request_clarification",
            "classify_incident": "classify_incident",
        }
    )

    builder.add_conditional_edges(
        "classify_incident",
        route_after_classification,
        {
            "human_review": "human_review",
            "retrieve_context": "retrieve_context",
        }
    )

    # Linear edges
    builder.add_edge("retrieve_context", "investigate_with_context")

    builder.add_conditional_edges(
        "investigate_with_context",
        route_after_investigation,
        {
            "human_review": "human_review",
            "auto_resolve": "auto_resolve",
        }
    )

    # Terminal edges
    builder.add_edge("request_clarification", END)
    builder.add_edge("human_review", END)
    builder.add_edge("auto_resolve", END)

    # Compile with memory checkpointer for state persistence
    checkpointer = MemorySaver()

    interrupt_before = ["human_review"] if interrupt_on_human_review else []

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
    )


# Singleton graph instance for production use
graph = build_graph(interrupt_on_human_review=True)
