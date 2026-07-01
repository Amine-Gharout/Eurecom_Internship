"""
Node 3: Templater — Jinja2 rendering, YAML merging, Owncast injection.
"""

import math
import os
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from .state import GraphState

# ---------------------------------------------------------------------------
# Jinja2 environment configuration
# ---------------------------------------------------------------------------
# ``trim_blocks=True`` strips the first newline after a block tag, and
# ``lstrip_blocks=True`` strips leading whitespace before a block tag.
# Both are **critical** to avoid indentation corruption in the rendered YAML.
# ``keep_trailing_newline=True`` preserves the final newline so the output
# is a well-formed text file.
# ---------------------------------------------------------------------------


def _build_jinja_env(template_dir: str) -> Environment:
    """Return a Jinja2 ``Environment`` configured for YAML-safe rendering."""
    return Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


# ---------------------------------------------------------------------------
# Resource heuristic
# ---------------------------------------------------------------------------


def _cpu_limit(throughput_mbps: int) -> float:
    """Map throughput to vCPU count: 1 vCPU per 500 Mbps, minimum 1."""
    return max(1.0, math.ceil(throughput_mbps / 500.0))


def _memory_limit_mb(throughput_mbps: int) -> int:
    """Map throughput to memory: 4 MB per Mbps, minimum 512 MB."""
    return max(512, throughput_mbps * 4)


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def _render_template(env: Environment, name: str, context: dict) -> str:
    """Render a single Jinja2 template and return its string output."""
    template = env.get_template(name)
    return template.render(context)


# ---------------------------------------------------------------------------
# YAML loading / dumping helpers
# ---------------------------------------------------------------------------


def _load_yaml(content: str) -> dict:
    """Parse a YAML string into a dict. Returns ``{}`` for empty input."""
    result = yaml.safe_load(content)
    if result is None:
        return {}
    return result


def _dump_yaml(data: dict) -> str:
    """Serialize a dict to a well-formatted YAML string."""

    class _LiteralStr(str):
        pass

    def _literal_representer(dumper, data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")

    yaml.add_representer(_LiteralStr, _literal_representer)

    return yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )


# ---------------------------------------------------------------------------
# Merge two docker-compose dicts
# ---------------------------------------------------------------------------


def _merge_compose_dicts(core: dict, gnbsim: dict) -> dict:
    """Shallow-merge two docker-compose dicts.

    - ``services`` are combined from both.
    - ``networks`` is taken from *core* (which defines the subnet); gnbsim's
      ``external: True`` is intentionally dropped.
    """

    merged: dict = {}

    # Merge top-level keys
    all_keys = set(core.keys()) | set(gnbsim.keys())

    for key in all_keys:
        if key == "services":
            merged[key] = {}
            merged[key].update(core.get("services", {}))
            merged[key].update(gnbsim.get("services", {}))
        elif key == "networks":
            # Always use core's network definition (has subnet/IPAM)
            merged[key] = core.get(key, gnbsim.get(key))
        else:
            merged[key] = core.get(key, gnbsim.get(key))

    return merged


# ---------------------------------------------------------------------------
# Owncast injection
# ---------------------------------------------------------------------------

_OWNCAST_SERVICE = {
    "container_name": "owncast",
    "image": "gabekangas/owncast:latest",
    "restart": "always",
    "cap_add": ["NET_ADMIN"],
    "ports": ["8081:8080", "1935:1935"],
    "networks": ["public_net"],
}


def _inject_owncast(services: dict) -> dict:
    """Append the Owncast service block, deduplicating by ``container_name``."""

    for svc in services.values():
        if isinstance(svc, dict) and svc.get("container_name") == "owncast":
            # Already present — do not inject a duplicate
            return services

    services["owncast"] = _OWNCAST_SERVICE
    return services


# ---------------------------------------------------------------------------
# Main node function
# ---------------------------------------------------------------------------


def render_compose(state: GraphState) -> GraphState:
    """Render Jinja2 templates, merge them, inject Owncast, and write output.

    Three templates are rendered with the same context:

    1. ``docker-compose-core.j2`` — the OAI 5G core network
    2. ``docker-compose-gnbsim.j2`` — the gnbsim UE simulators
    3. ``basic_nrf_config.j2`` — the OAI NRF configuration YAML

    Output files written to ``deployments/``:

    - ``basic_nrf_config.yaml`` — rendered NRF config
    - ``final-deploy.yaml`` — merged docker-compose for deployment
    """

    slos = state["extracted_slos"]
    template_dir = state["template_base_path"]
    output_dir = state["output_path"]

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # --- Build template context ---
    throughput = slos["target_throughput_mbps"]
    latency = slos["target_latency_ms"]

    context = {
        "target_latency_ms": latency,
        "target_throughput_mbps": throughput,
        "cpu_limit": _cpu_limit(throughput),
        "memory_limit_mb": _memory_limit_mb(throughput),
    }

    env = _build_jinja_env(template_dir)

    # --- Render all three templates ---

    # 1. NRF config (must be written first — compose mounts it as a volume)
    try:
        config_rendered = _render_template(env, "basic_nrf_config.j2", context)
    except Exception:
        # Template may not exist yet (user hasn't created it) — non-fatal
        config_rendered = None

    if config_rendered:
        config_path = os.path.join(output_dir, "basic_nrf_config.yaml")
        with open(config_path, "w", encoding="utf-8") as fh:
            fh.write(config_rendered)

    # 2. Core compose
    core_raw = _render_template(env, "docker-compose-core.j2", context)
    core_dict = _load_yaml(core_raw) or {}

    # 3. gnbsim compose
    gnbsim_raw = _render_template(env, "docker-compose-gnbsim.j2", context)
    gnbsim_dict = _load_yaml(gnbsim_raw) or {}

    # --- Merge and inject Owncast ---
    merged = _merge_compose_dicts(core_dict, gnbsim_dict)
    merged["services"] = _inject_owncast(merged.get("services", {}))

    # --- Serialize to final-deploy.yaml ---
    final_yaml = _dump_yaml(merged)
    compose_path = os.path.join(output_dir, "final-deploy.yaml")
    with open(compose_path, "w", encoding="utf-8") as fh:
        fh.write(final_yaml)

    return state
