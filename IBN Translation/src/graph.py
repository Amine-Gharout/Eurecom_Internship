"""
LangGraph state machine assembly for the IBN pipeline.

Nodes:
    1. extract  — LLM parses NL intent → structured SLOs
    2. validate — pure-Python guardrails on SLO values
    3. template — Jinja2 render + YAML merge + Owncast injection
    4. deploy   — ``docker compose up -d`` + health check
    5. handle_error — terminal error node

Conditional routing:
    After ``validate``, if ``error_message`` is non-empty the graph
    routes to ``handle_error`` instead of ``template``.
"""

from langgraph.graph import END, StateGraph

from .activator import deploy_infrastructure
from .extractor import extract_intent
from .state import GraphState
from .templater import render_compose
from .validator import validate_slos


def _should_continue(state: GraphState) -> str:
    """Conditional edge: ``"handle_error"`` if validation failed, else ``"template"``."""
    if state.get("error_message", ""):
        return "handle_error"
    return "template"


def _handle_error(state: GraphState) -> GraphState:
    """Terminal error node — logs the error and marks deployment as failed."""
    state["deployment_status"] = "failed"
    return state


def build_graph() -> StateGraph:
    """Construct and compile the IBN LangGraph state machine.

    Returns a compiled graph ready for ``.invoke()``.
    """

    builder = StateGraph(GraphState)

    # Register nodes
    builder.add_node("extract", extract_intent)
    builder.add_node("validate", validate_slos)
    builder.add_node("template", render_compose)
    builder.add_node("deploy", deploy_infrastructure)
    builder.add_node("handle_error", _handle_error)

    # Edges
    builder.set_entry_point("extract")
    builder.add_edge("extract", "validate")

    builder.add_conditional_edges(
        "validate",
        _should_continue,
        {
            "template": "template",
            "handle_error": "handle_error",
        },
    )

    builder.add_edge("template", "deploy")
    builder.add_edge("deploy", END)
    builder.add_edge("handle_error", END)

    return builder.compile()
