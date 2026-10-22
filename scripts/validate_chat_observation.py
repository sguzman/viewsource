#!/usr/bin/env python3
"""Strict validation of hand-curated structural chat observations.

Never capture content. Never automatically promote validated data into an
observed-live claim: a reviewer must independently verify each observation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

TOP = {"format_version", "feature_id", "experiment_type", "evidence_status",
       "privacy_boundary", "steps"}
STEP = {"ordinal", "offset_ms", "event", "source", "selection", "response_phase",
        "message_count_delta", "conversation_count_delta", "parent_link_delta", "result"}
EVENT = {"select_conversation", "clear_selection", "edit_draft", "submit_draft",
         "response_started", "response_completed", "stop_response", "response_failed",
         "retry_response", "edit_message", "regenerate", "branch_new_chat", "reload", "other"}
SOURCE = {"synthetic_user_action", "visible_ui_change", "sanitized_transport_signal", "unknown"}
SELECTION = {"none", "selected", "unknown"}
RESPONSE = {"idle", "editing", "sending", "receiving", "complete", "failed", "stopped", "unknown"}
RESULT = {"observed", "not_observed", "inconclusive"}


def validate(doc: dict) -> list[str]:
    errors = []
    if not isinstance(doc, dict) or set(doc) != TOP:
        return ["Document must have exactly the allowed top-level keys"]
    for key, expected in (("format_version", 1), ("feature_id", "chat-interaction"),
                          ("experiment_type", "disposable_synthetic"),
                          ("evidence_status", "unreviewed"),
                          ("privacy_boundary", "structural_counts_and_fixed_event_labels_only")):
        if type(doc[key]) is not type(expected) or doc[key] != expected:
            errors.append("Invalid fixed field: " + key)
    steps = doc["steps"]
    if not isinstance(steps, list) or not (1 <= len(steps) <= 300):
        return errors + ["Steps must be a bounded nonempty list"]
    last = -1
    for index, entry in enumerate(steps):
        prefix = f"step {index}: "
        if not isinstance(entry, dict) or set(entry) != STEP:
            errors.append(prefix + "unapproved keys or missing keys")
            continue
        for field, variants in (("event", EVENT), ("source", SOURCE),
                                ("selection", SELECTION), ("response_phase", RESPONSE),
                                ("result", RESULT)):
            if not isinstance(entry[field], str) or entry[field] not in variants:
                errors.append(prefix + "invalid enumeration: " + field)
        ordinal, offset = entry["ordinal"], entry["offset_ms"]
        if type(ordinal) is not int or ordinal != index:
            errors.append(prefix + "steps must have sequential ordinals")
        if type(offset) is not int or not (0 <= offset <= 3600000) or offset < last:
            errors.append(prefix + "invalid nondecreasing relative time")
        if type(offset) is int:
            last = offset
        for key in ("message_count_delta", "conversation_count_delta", "parent_link_delta"):
            count = entry[key]
            if type(count) is not int or not (-100 <= count <= 100):
                errors.append(prefix + "invalid bounded structural count: " + key)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate content-free chat research observation")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        doc = json.loads(args.file.read_text(encoding="utf-8"))
        errors = validate(doc)
    except (OSError, ValueError) as exc:
        parser.exit(2, "Invalid research input: " + str(exc) + "\n")
    if errors:
        parser.exit(2, "Invalid observation: " + "; ".join(errors) + "\n")
    print("Structurally valid, not independently verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
