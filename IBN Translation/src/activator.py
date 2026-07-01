"""
Node 4: Activator — deploys the generated docker-compose YAML
and performs a basic health check.
"""

import subprocess
import time

from .state import GraphState

# ---------------------------------------------------------------------------
# Containers whose presence & health are verified post-deployment
# ---------------------------------------------------------------------------
_REQUIRED_CONTAINERS = {"oai-amf", "oai-upf", "owncast"}

# Seconds to wait after ``docker compose up -d`` before running health checks.
_WAIT_SECONDS = 10


def deploy_infrastructure(state: GraphState) -> GraphState:
    """Deploy ``final-deploy.yaml`` via ``docker compose`` and verify health.

    Steps
    -----
    1. ``docker compose -f <output_path>/final-deploy.yaml up -d``
    2. Wait ``_WAIT_SECONDS`` for containers to initialize.
    3. ``docker ps`` — verify ``oai-amf``, ``oai-upf``, and ``owncast``
       are running (status does not contain ``Exited`` or ``Restarting``).
    """

    compose_file = f"{state['output_path']}/final-deploy.yaml"

    # ---- Step 1: deploy ----
    result = subprocess.run(
        ["docker", "compose", "-f", compose_file, "up", "-d"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        state["deployment_status"] = "failed"
        state["error_message"] = (
            f"docker compose up failed (rc={result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        return state

    # ---- Step 2: wait for initialization ----
    time.sleep(_WAIT_SECONDS)

    # ---- Step 3: health check ----
    ps_result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}} {{.Status}}"],
        capture_output=True,
        text=True,
    )

    if ps_result.returncode != 0:
        state["deployment_status"] = "failed"
        state["error_message"] = (
            f"docker ps failed (rc={ps_result.returncode}):\n{ps_result.stderr}"
        )
        return state

    # Parse ``docker ps`` output into {container_name: status_line}
    running: dict[str, str] = {}
    for line in ps_result.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            running[parts[0]] = parts[1]

    # Verify required containers
    missing = []
    unhealthy = []
    for name in _REQUIRED_CONTAINERS:
        if name not in running:
            missing.append(name)
            continue
        status = running[name].lower()
        if "exited" in status or "restarting" in status:
            unhealthy.append(f"{name} ({running[name]})")

    if missing or unhealthy:
        state["deployment_status"] = "failed"
        msg_parts = []
        if missing:
            msg_parts.append(f"Missing containers: {', '.join(missing)}")
        if unhealthy:
            msg_parts.append(f"Unhealthy containers: {', '.join(unhealthy)}")
        state["error_message"] = " | ".join(msg_parts)
        return state

    state["deployment_status"] = "success"
    return state
