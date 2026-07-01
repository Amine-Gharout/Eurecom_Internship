"""
Node 1: Extractor — uses an LLM (DeepSeek via ChatOpenAI) with
JSON-mode prompting to parse a natural-language intent into
a structured ``NetworkIntent``.

Because DeepSeek does not support OpenAI's ``response_format``
structured-output feature, we use a system prompt that instructs the
model to reply with **only** a JSON object matching the schema.
The response is then parsed and validated via Pydantic.
"""

import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError

from .state import GraphState


class NetworkIntent(BaseModel):
    """Pydantic schema capturing the networking SLOs from a user intent."""

    application_name: str = Field(
        default="owncast",
        description="Name of the application to deploy (e.g., owncast)",
    )
    target_latency_ms: int = Field(
        description="Target end-to-end latency in milliseconds",
    )
    target_throughput_mbps: int = Field(
        description="Target throughput in megabits per second (Mbps)",
    )


_EXTRACTOR_SYSTEM_PROMPT = """\
You are a networking SLO extraction assistant. Given a natural-language
intent describing a 5G network deployment, extract the following fields
and return them as a **JSON object only** — no markdown, no explanation.

Schema:
{
  "application_name": "string (default: owncast)",
  "target_latency_ms": integer,
  "target_throughput_mbps": integer
}

Rules:
- If a field is not mentioned in the intent, use the default.
- ``target_latency_ms`` must be in milliseconds.
- ``target_throughput_mbps`` must be in megabits per second.
- Reply with the JSON object ONLY. No other text."""


def _build_llm() -> ChatOpenAI:
    """Instantiate the LLM client.

    Reads configuration from environment variables:

    - ``DEEPSEEK_API_KEY`` — required (passed as ``api_key``)
    - ``IBN_LLM_MODEL`` — defaults to ``deepseek-chat``
    - ``IBN_LLM_BASE_URL`` — defaults to ``https://api.deepseek.com/v1``
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY environment variable is not set. "
            "Set it to your DeepSeek API key, or override IBN_LLM_MODEL "
            "and IBN_LLM_BASE_URL for a different provider."
        )

    model = os.environ.get("IBN_LLM_MODEL", "deepseek-chat")
    base_url = os.environ.get(
        "IBN_LLM_BASE_URL", "https://api.deepseek.com/v1")

    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=0.0,
    )


def _extract_json_from_response(text: str) -> str:
    """Extract a JSON object string from an LLM response.

    Handles responses wrapped in markdown fences (`` ```json ... ``` ``)
    as well as raw JSON.
    """
    # Try markdown code fence first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: find the first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return text.strip()


def extract_intent(state: GraphState) -> GraphState:
    """Parse ``raw_intent`` into a structured ``NetworkIntent`` via LLM.

    Sends a system prompt with the JSON schema, parses the model's text
    response as JSON, validates with Pydantic, and stores the result in
    ``state["extracted_slos"]`` as a plain dict.
    """

    llm = _build_llm()

    messages = [
        SystemMessage(content=_EXTRACTOR_SYSTEM_PROMPT),
        HumanMessage(content=state["raw_intent"]),
    ]

    response = llm.invoke(messages)
    raw_text = response.content if hasattr(
        response, "content") else str(response)

    # Parse JSON from the response text
    json_str = _extract_json_from_response(raw_text)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Failed to parse JSON from LLM response. "
            f"Raw response:\n{raw_text}\n"
            f"Extracted JSON:\n{json_str}"
        ) from exc

    try:
        parsed = NetworkIntent.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError(
            f"LLM response did not match NetworkIntent schema. "
            f"Parsed data: {data}"
        ) from exc

    state["extracted_slos"] = parsed.model_dump()
    return state
