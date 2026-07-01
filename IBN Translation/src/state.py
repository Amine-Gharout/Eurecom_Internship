"""
LangGraph state definition for the IBN (Intent-Based Networking) pipeline.
"""

from typing import TypedDict


class GraphState(TypedDict):
    """State object passed between LangGraph nodes.

    Attributes:
        raw_intent: The natural-language intent string from the user.
        extracted_slos: Parsed SLOs as a dict with keys:
            ``application_name``, ``target_latency_ms``, ``target_throughput_mbps``.
        template_base_path: Filesystem path to the ``templates/`` directory.
        output_path: Filesystem path where ``final-deploy.yaml`` is written.
        deployment_status: One of ``""`` (pending), ``"success"``, or ``"failed"``.
        error_message: Human-readable error description; empty string when no error.
    """

    raw_intent: str
    extracted_slos: dict
    template_base_path: str
    output_path: str
    deployment_status: str
    error_message: str
