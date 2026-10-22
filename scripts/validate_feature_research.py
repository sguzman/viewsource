"""Validate an independent feature research queue without reopening ZIP tasks."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOWED_DIRS=("scripts/","tests/","site/","docs/","schemas/","specimens/","queues/")


def validate_feature_research(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    def require(ok: bool, reason: str) -> None:
        if not ok:
            errors.append(reason)

    file = root / "queues/chat_research.json"
    if not file.exists():
        return ["Chat feature backlog missing"]
    data=json.loads(file.read_text(encoding="utf-8"))
    require(data.get("format_version")==1, "Chat feature backlog version")
    require(data.get("feature_id")=="chat-interaction", "Chat backlog feature ID")
    require(data.get("specimen_id")=="chatgpt-com" and data.get("version")==2,
            "Chat backlog specimen/version")
    tasks=data.get("tasks",[])
    ids=[t["id"] for t in tasks]
    require(len(ids)==len(set(ids)), "Duplicate chat task IDs")
    by_id={t["id"]:t for t in tasks}
    specimen=root / "specimens/chatgpt-com/v0002/record.json"
    record=json.loads(specimen.read_text(encoding="utf-8"))
    evidence={f["evidence"].get("evidence_ref") for f in record["findings"]}
    for task in tasks:
        ident=task["id"]
        require(task.get("feature_id")=="chat-interaction"
                and task.get("specimen_id")=="chatgpt-com"
                and task.get("version")==2,
                "Mismatched feature task: "+ident)
        require(task.get("scope") in {"offline","runtime"}, "Bad feature scope: "+ident)
        require(task.get("status") in {"queued","done","requires_new_evidence"},
                "Bad feature status: "+ident)
        require(bool(task.get("title")) and bool(task.get("acceptance")),
                "Unscoped feature task: "+ident)
        references=task.get("evidence_refs",[])
        require(set(references)<=evidence, "Ungrounded feature evidence: "+ident)
        require(len(references)==len(set(references)), "Repeated feature evidence: "+ident)
        artifacts=task.get("artifacts",[])
        require(len(artifacts)==len(set(artifacts)), "Repeated feature artifacts: "+ident)
        for path in artifacts:
            safe=(isinstance(path,str) and path.startswith(ALLOWED_DIRS)
                  and ".." not in Path(path).parts and (root / path).is_file())
            require(safe, "Missing or unsafe feature artifact: "+ident)
        if task["status"]=="done":
            require(bool(references or artifacts), "Completed chat task needs support: "+ident)
        elif task["status"]=="requires_new_evidence":
            require(task["scope"]=="runtime", "Offline task cannot claim new runtime prerequisite: "+ident)
            require(not references, "Blocked feature task cannot claim observed evidence: "+ident)
            require(not artifacts, "Blocked feature task cannot claim delivered runtime artifacts: "+ident)
        for dep in task["depends_on"]:
            require(dep in by_id and dep != ident,"Unknown or self-dependent feature task: "+ident)
    visited=set()
    active=set()
    def visit(key):
        if key in active:
            errors.append("Cyclic feature task dependencies")
            return
        if key in visited:
            return
        active.add(key)
        for dep in by_id[key]["depends_on"]:
            if dep in by_id:
                visit(dep)
        active.remove(key)
        visited.add(key)
    for ident in by_id:
        visit(ident)
    return errors
