#!/usr/bin/env python3
"""Summarize strictly structural observations against candidate chat events.

No browser access, no site calls, no captured content, and no automatic
promotion of a hypothetical transition to independently verified behavior.
Input uses only the fixed, content-free chat observation schema.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from validate_chat_observation import validate

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT / "specimens/chatgpt-com/v0002/chat-interaction.graph.json"

# The observation vocabulary and the candidate graph event vocabulary differ.
# Only explicit, audited mappings are allowed. A match is NOT verified dataflow.
EVENT_MAPPING = {
    "select_conversation": ("select_conversation",),
    "clear_selection": ("clear_selection",),
    "edit_draft": ("edit_draft",),
    "submit_draft": ("submit_draft",),
    "response_started": ("response_started",),
    "response_completed": ("response_completed",),
    "stop_response": ("stop_response",),
    "response_failed": ("response_failed",),
    "retry_response": ("retry_response",),
    "edit_message": ("start_message_edit", "submit_message_edit"),
    "regenerate": ("request_regeneration",),
}


class ObservationError(ValueError):
    """The observation cannot be used as structural research input."""


def compare_sequence(observation: dict, graph: dict) -> dict:
    """Check coarse observations against *candidate* state transitions only.

    No observed trace can verify an internal handler or causal relationship.
    Initial states are hypothetical; later state labels come from the supplied
    structural observations rather than assumed model progress.
    """
    states = {
        "selection": "none",
        "response": "idle",
    }
    previous_basis = {
        "selection": "assumed_initial_state",
        "response": "assumed_initial_state",
    }
    declared = {t["event"] for t in graph["transitions"]}
    rows = []
    counts = Counter()
    for i, step in enumerate(observation["steps"]):
        source_event = step["event"]
        matching_events = [e for e in EVENT_MAPPING.get(source_event, ()) if e in declared]
        candidates = [t for t in graph["transitions"] if t["event"] in matching_events]
        reported = {"selection": step["selection"], "response": step["response_phase"]}
        # Never treat a user-visible label as a recovered internal state.
        comparable = [t for t in candidates if t["machine"] in states]
        matches = [t for t in comparable if
                   t["from"] == states[t["machine"]]]
        if not candidates:
            status = "unmapped"
        elif not comparable:
            status = "insufficient_state_signal"
        elif len(matches) == 0:
            status = "no_matching_candidate_edge"
        elif len(matches) != 1:
            status = "ambiguous_candidate_edges"
        else:
            edge = matches[0]
            value = reported[edge["machine"]]
            if value == "unknown":
                status = "insufficient_state_signal"
            elif value == edge["to"]:
                status = "consistent_with_candidate"
            else:
                status = "conflicts_with_candidate"
        rows.append({
            "ordinal": i,
            "event": source_event,
            "status": status,
            "candidate_transition_ids": sorted(t["id"] for t in matches),
            "source_state_basis": {
                machine: previous_basis[machine] for machine in states
                if any(t["machine"] == machine for t in comparable)
            },
            "internal_behavior_verified": False,
        })
        counts[status] += 1
        for machine, value in reported.items():
            if value != "unknown":
                states[machine] = value
                previous_basis[machine] = "prior_coarse_observation"
            else:
                # Unknown means we cannot safely claim continuity of that
                # machine's state through the gap.
                states[machine] = None
                previous_basis[machine] = "unknown"
    return {
        "basis": "hypothetical_machine_comparison",
        "verified_transitions": 0,
        "status_counts": dict(sorted(counts.items())),
        "steps": rows,
    }


def summarize(observation: dict, graph: dict) -> dict:
    problems = validate(observation)
    if problems:
        raise ObservationError("Rejected observation: " + "; ".join(problems))
    if graph.get("feature_id") != "chat-interaction":
        raise ObservationError("Wrong feature graph")
    known = {event["id"] for event in graph["events"]}
    candidate_edges = graph["transitions"]

    counts = Counter(step["event"] for step in observation["steps"])
    results = Counter(step["result"] for step in observation["steps"])
    phases = Counter(step["response_phase"] for step in observation["steps"])
    observed_classes = []
    for event in sorted(counts):
        matches = [candidate for candidate in EVENT_MAPPING.get(event, ())
                   if candidate in known]
        edge_ids = sorted(t["id"] for t in candidate_edges if t["event"] in matches)
        observed_classes.append({
            "event": event,
            "occurrences": counts[event],
            "candidate_event_ids": matches,
            "candidate_transition_ids": edge_ids,
            "mapping_status": "candidate_only" if edge_ids else "unmapped",
        })
    steps = observation["steps"]
    return {
        "feature_id": "chat-interaction",
        "source_kind": "unreviewed_structural_observation",
        "verified_transition_count": 0,
        "transition_promotion_allowed": False,
        "step_count": len(steps),
        "duration_ms": steps[-1]["offset_ms"] - steps[0]["offset_ms"],
        "result_counts": {name: results[name] for name in
                          ("observed", "not_observed", "inconclusive")},
        "phase_counts": {name: phases[name] for name in sorted(phases)},
        "structure_deltas": {
            "messages": sum(s["message_count_delta"] for s in steps),
            "conversations": sum(s["conversation_count_delta"] for s in steps),
            "parent_links": sum(s["parent_link_delta"] for s in steps),
        },
        "candidate_event_correlations": observed_classes,
        "candidate_sequence_alignment": compare_sequence(observation, graph),
        "limits": [
            "Matching event names does not confirm action-handler ownership or causal dataflow.",
            "A structural observation, including an observed result label, is not a verified transition.",
            "No server schema, network endpoint, conversation ID or message content was inspected.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize sanitized candidate chat observations")
    parser.add_argument("observation", type=Path)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    args = parser.parse_args()
    try:
        observation = json.loads(args.observation.read_text("utf-8"))
        graph = json.loads(args.graph.read_text("utf-8"))
        result = summarize(observation, graph)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, "Observation rejected: " + str(exc) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
