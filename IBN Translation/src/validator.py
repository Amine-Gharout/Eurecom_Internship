"""
Node 2: Validator — pure-Python guardrails for extracted SLOs.
"""

from .state import GraphState


def validate_slos(state: GraphState) -> GraphState:
    """Validate that ``target_latency_ms`` is positive and
    ``target_throughput_mbps`` is within a realistic bound (0, 1000].

    On failure populates ``error_message`` so the graph's conditional edge
    routes to the error handler.
    """

    slos = state["extracted_slos"]

    latency = slos.get("target_latency_ms")
    throughput = slos.get("target_throughput_mbps")

    if latency is None or latency <= 0:
        state["error_message"] = (
            f"Validation failed: target_latency_ms must be > 0, got {latency}"
        )
        return state

    if throughput is None or throughput <= 0:
        state["error_message"] = (
            f"Validation failed: target_throughput_mbps must be > 0, got {throughput}"
        )
        return state

    if throughput > 1000:
        state["error_message"] = (
            f"Validation failed: target_throughput_mbps must be <= 1000, got {throughput}"
        )
        return state

    # All checks passed — error_message stays empty
    return state
