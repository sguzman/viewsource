#!/usr/bin/env python3
"""Read Viewsource's synthetic feature transitions without controlling a website.

The model never performs IO beyond loading an authored JSON graph. In
particular, it never invokes browser controls or treats hypotheses as actions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT / "specimens/chatgpt-com/v0002/chat-interaction.graph.json"


class FeatureGraphError(ValueError):
    """A malformed graph reference or attempted unverified transition."""


class FeatureGraphModel:
    def __init__(self, graph: dict[str, Any]) -> None:
        self.graph = graph
        self.machines = {m["id"]: m for m in graph["machines"]}
        self.events = {e["id"]: e for e in graph["events"]}
        self.transitions = {t["id"]: t for t in graph["transitions"]}
        if len(self.machines) != len(graph["machines"]):
            raise FeatureGraphError("Repeated machine key")
        if len(self.events) != len(graph["events"]):
            raise FeatureGraphError("Repeated event key")
        if len(self.transitions) != len(graph["transitions"]):
            raise FeatureGraphError("Repeated transition key")
        self.entities = {e["id"]: e for e in graph["entities"]}
        self.domain_relations = graph.get("domain_relations", [])
        for rel in self.domain_relations:
            if rel["from"] not in self.entities or rel["to"] not in self.entities:
                raise FeatureGraphError("Unknown domain entity in relation")
            if rel["evidence_status"] not in {"hypothesis", "observed_live"}:
                raise FeatureGraphError("Unrecognized domain relation evidence")
            if rel["evidence_status"] == "hypothesis" and rel["verified_evidence_refs"]:
                raise FeatureGraphError("Hypothetical relationship cannot carry verified evidence")
        for machine in graph["machines"]:
            allowed = {s["id"] for s in machine["states"]}
            if machine["initial_state"] not in allowed or len(allowed) != len(machine["states"]):
                raise FeatureGraphError("Invalid machine states")
        for transition in graph["transitions"]:
            machine = self.machines.get(transition["machine"])
            if not machine:
                raise FeatureGraphError("Unknown machine")
            allowed = {s["id"] for s in machine["states"]}
            if transition["from"] not in allowed or transition["to"] not in allowed:
                raise FeatureGraphError("Unknown transition state")
            if transition["event"] not in self.events:
                raise FeatureGraphError("Unknown event")
            if transition["evidence_status"] not in {"hypothesis", "observed_live"}:
                raise FeatureGraphError("Unrecognized transition evidence")

    @classmethod
    def from_file(cls, path: Path = DEFAULT_GRAPH) -> FeatureGraphModel:
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def query(self, machine: str, *, from_state: str | None = None,
              event: str | None = None) -> list[dict[str, Any]]:
        if machine not in self.machines:
            raise FeatureGraphError("Unknown machine")
        if from_state is not None and from_state not in {
                s["id"] for s in self.machines[machine]["states"]}:
            raise FeatureGraphError("Unknown state")
        if event is not None and event not in self.events:
            raise FeatureGraphError("Unknown event")
        return [t for t in self.graph["transitions"]
                if t["machine"] == machine
                and (from_state is None or t["from"] == from_state)
                and (event is None or t["event"] == event)]

    def resolve_verified(self, machine: str, from_state: str,
                         event: str) -> dict[str, Any]:
        """Return evidence-backed metadata, NEVER execute an action.

        No guessed transition is silently accepted. Guards are exposed for
        caller review and are not evaluated by this research-only library.
        """
        candidates = self.query(machine, from_state=from_state, event=event)
        if len(candidates) != 1:
            raise FeatureGraphError("Transition absent or ambiguous")
        transition = candidates[0]
        if transition["evidence_status"] != "observed_live" or not transition["evidence_refs"]:
            raise FeatureGraphError("Transition has no independent live verification")
        return transition

    def to_domain_dot(self) -> str:
        """Return an illustrative entity graph, never an executable site map."""
        lines = ["digraph domain {", '  label="Hypothetical chat entity relationships";',
                 "  rankdir=LR;"]
        for entity in self.graph["entities"]:
            lines.append("  " + json.dumps(entity["id"]) + " [shape=box];")
        for relation in self.domain_relations:
            style = "dashed" if relation["evidence_status"] == "hypothesis" else "solid"
            lines.append("  " + json.dumps(relation["from"]) + " -> " +
                         json.dumps(relation["to"]) + " [style=" + style +
                         ",label=" + json.dumps(relation["predicate"]) + "];")
        return "\n".join(lines + ["}"])

    def to_dot(self, machine: str) -> str:
        if machine not in self.machines:
            raise FeatureGraphError("Unknown machine")
        def escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        lines = ["digraph feature {", '  label="Candidate feature model";', "  rankdir=LR;"]
        for state in self.machines[machine]["states"]:
            lines.append(f'  "{escape(state["id"])}" [shape=box];')
        for t in self.query(machine):
            style = "solid" if t["evidence_status"] == "observed_live" else "dashed"
            event = self.events[t["event"]]["label"]
            lines.append(f'  "{escape(t["from"])}" -> "{escape(t["to"])}" '
                         f'[style={style},label="{escape(event)}"];')
        return "\n".join(lines + ["}"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect non-executable feature transition evidence")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--machine", default="response")
    parser.add_argument("--domain", action="store_true",help="Inspect entity relations instead of state machines")
    parser.add_argument("--state", default=None)
    parser.add_argument("--event", default=None)
    parser.add_argument("--format", choices=("json", "dot"), default="json")
    parser.add_argument("--resolve-verified", action="store_true",
                        help="Fail closed unless exactly one independently verified edge exists")
    args = parser.parse_args()
    try:
        model = FeatureGraphModel.from_file(args.graph)
        if args.domain and args.resolve_verified:
            raise FeatureGraphError("Domain research cannot be executed")
        if args.domain:
            output = model.to_domain_dot() if args.format == "dot" else {
                "feature_id": model.graph["feature_id"],
                "source_scope": model.graph["source_scope"],
                "execution_supported": False,
                "entities": model.graph["entities"],
                "relations": model.domain_relations
            }
        elif args.resolve_verified:
            if args.state is None or args.event is None:
                raise FeatureGraphError("A source state and event are required")
            output: Any = model.resolve_verified(args.machine, args.state, args.event)
        elif args.format == "dot":
            output = model.to_dot(args.machine)
        else:
            output = {
                "machine": args.machine,
                "source_scope": model.graph["source_scope"],
                "execution_supported": False,
                "transitions": model.query(args.machine, from_state=args.state, event=args.event)
            }
    except (FeatureGraphError, OSError, ValueError, KeyError) as exc:
        parser.exit(2, "Cannot resolve feature graph: " + str(exc) + "\n")
    print(output if isinstance(output, str) else json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
