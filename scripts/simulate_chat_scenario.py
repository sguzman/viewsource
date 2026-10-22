#!/usr/bin/env python3
"""Run explicitly hypothetical chat state-machine scenarios with no site access.

This simulator is for designing software, never for executing UI actions.
It does not inspect or store messages, URLs, account data or runtime traces.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from chat_feature_cli import FeatureGraphModel, FeatureGraphError


class ScenarioError(ValueError):
    """An invalid or ambiguous scenario that cannot be simulated."""


def simulate(graph: dict, scenario: dict, *, assume_guards: bool = False) -> dict:
    if not isinstance(scenario, dict) or set(scenario) != {"format_version", "steps"}:
        raise ScenarioError("Only format_version and steps are permitted")
    if type(scenario["format_version"]) is not int or scenario["format_version"] != 1:
        raise ScenarioError("Unexpected scenario version")
    steps = scenario["steps"]
    if not isinstance(steps, list) or len(steps) > 100:
        raise ScenarioError("Scenario must have at most 100 steps")
    model = FeatureGraphModel(graph)
    states = {key: machine["initial_state"] for key, machine in model.machines.items()}
    trace = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) != {"machine", "event"}:
            raise ScenarioError("Scenario step contains missing or extra fields")
        machine, event = step["machine"], step["event"]
        if not isinstance(machine, str) or not isinstance(event, str):
            raise ScenarioError("Scenario steps need fixed machine and event strings")
        if machine not in states:
            raise ScenarioError("Unknown machine")
        source = states[machine]
        try:
            choices = model.query(machine, from_state=source, event=event)
        except FeatureGraphError as exc:
            raise ScenarioError(str(exc)) from exc
        if len(choices) != 1:
            raise ScenarioError("No unique candidate transition at step " + str(i))
        edge = choices[0]
        if edge["evidence_status"] != "hypothesis":
            raise ScenarioError("This simulator accepts candidate transitions only")
        guards = edge["guards"]
        if guards and not assume_guards:
            raise ScenarioError("Guard assumptions required at step " + str(i))
        states[machine] = edge["to"]
        trace.append({
            "step": i, "machine": machine, "event": event,
            "from_state": source, "to_state": edge["to"],
            "candidate_transition": edge["id"],
            "assumed_guards": list(guards),
            "evidence_status": "hypothetical_simulation",
        })
    return {
        "model_type": "synthetic_hypothetical_only",
        "verified_runtime_behavior": False,
        "performed_site_actions": False,
        "machine_states": states,
        "trace": trace,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate a hypothetical chat feature state path")
    parser.add_argument("scenario", type=Path, help="Content-free synthetic JSON event sequence")
    parser.add_argument("--graph", type=Path, default=Path(__file__).resolve().parents[1] /
                        "specimens/chatgpt-com/v0002/chat-interaction.graph.json")
    parser.add_argument("--assume-guards", action="store_true",
                        help="Explicitly assume unverified UI guards for model exploration")
    args = parser.parse_args()
    try:
        graph = json.loads(args.graph.read_text("utf-8"))
        scenario = json.loads(args.scenario.read_text("utf-8"))
        result = simulate(graph, scenario, assume_guards=args.assume_guards)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, "Scenario rejected: " + str(exc) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
