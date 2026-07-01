"""
CLI entry point for the IBN (Intent-Based Networking) pipeline.

Usage::

    cd "IBN Translation"
    python -m src --intent "Deploy a private 5G network for live streaming \\
                         ensuring 20ms latency and 200Mbps throughput"

    # Optional overrides
    python -m src \\
        --intent "..." \\
        --template-dir ./templates \\
        --output-dir ./deployments
"""

import argparse
import os
import sys
from pathlib import Path

from .graph import build_graph
from .state import GraphState

# Resolve defaults relative to the *package* directory (``src/``)
_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_TEMPLATE_DIR = str(_PACKAGE_DIR.parent / "templates")
_DEFAULT_OUTPUT_DIR = str(_PACKAGE_DIR.parent / "deployments")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="IBN Pipeline — translate NL intent → 5G deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--intent",
        "-i",
        required=True,
        help="Natural-language intent string (e.g., 'Deploy a private 5G...')",
    )
    parser.add_argument(
        "--template-dir",
        default=_DEFAULT_TEMPLATE_DIR,
        help=f"Path to Jinja2 templates directory (default: {_DEFAULT_TEMPLATE_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Path where final-deploy.yaml is written (default: {_DEFAULT_OUTPUT_DIR})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # Validate paths exist
    if not os.path.isdir(args.template_dir):
        print(
            f"ERROR: template directory does not exist: {args.template_dir}",
            file=sys.stderr,
        )
        return 1

    # Build initial state
    initial_state: GraphState = {
        "raw_intent": args.intent,
        "extracted_slos": {},
        "template_base_path": args.template_dir,
        "output_path": args.output_dir,
        "deployment_status": "",
        "error_message": "",
    }

    graph = build_graph()

    print("=" * 60)
    print("IBN Pipeline")
    print("=" * 60)
    print(f"Intent: {args.intent}")
    print(f"Templates: {args.template_dir}")
    print(f"Output: {args.output_dir}")
    print("-" * 60)

    # Run the graph
    final_state = graph.invoke(initial_state)

    # Report
    print()
    print("-" * 60)

    slos = final_state.get("extracted_slos", {})
    print(
        f"Extracted SLOs: "
        f"app={slos.get('application_name')}, "
        f"latency={slos.get('target_latency_ms')}ms, "
        f"throughput={slos.get('target_throughput_mbps')}Mbps"
    )

    status = final_state.get("deployment_status", "unknown")
    error = final_state.get("error_message", "")

    if error:
        print(f"ERROR: {error}")

    print(f"Deployment status: {status}")
    print("=" * 60)

    return 0 if status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
