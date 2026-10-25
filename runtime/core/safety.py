"""Fail-closed dispatch policy and local data containment."""
from __future__ import annotations
import fnmatch
import re
from pathlib import Path, PureWindowsPath
from .contracts import CoreError, content_hash


def safe_path(root: str | Path, relative: str) -> Path:
    base = Path(root).resolve()
    win = PureWindowsPath(relative)
    if not relative or Path(relative).is_absolute() or win.is_absolute() or win.drive or ".." in relative.replace("\\", "/").split("/") or ":" in relative:
        raise CoreError("Unsafe artifact path")
    candidate = (base / relative).resolve()
    if not candidate.is_relative_to(base) or candidate == base:
        raise CoreError("Artifact path escapes root")
    return candidate


def redact(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if re.search(r"(?i)(secret|password|token|api.?key|authorization|credential)", k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]", value)
        value = re.sub(r"\b(?:sk-[A-Za-z0-9_-]{8,}|AKIA[A-Z0-9]{16})\b", "[REDACTED]", value)
        value = re.sub(r"(?i)(api[_ -]?key|password|secret|token)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", value)
    return value


def guardian(role: str, action: str, resource: str, arguments: dict, rules: list[dict], *, forbidden_actions=(), sensitivity="PUBLIC", approvals=()) -> dict:
    action_hash = content_hash({"role": role, "action": action, "resource": resource, "arguments": arguments, "sensitivity": sensitivity})
    def answer(decision, reason):
        return {"decision": decision, "reason": reason, "action_hash": action_hash}
    if action not in {"model.reason", "files.read", "artifact.write"} or action in forbidden_actions:
        return answer("DENY", "Action unsupported or forbidden")
    matched = [r for r in rules if fnmatch.fnmatchcase(role, r.get("role", "")) and fnmatch.fnmatchcase(action, r.get("action", "")) and fnmatch.fnmatchcase(resource, r.get("resource", ""))]
    if not matched:
        return answer("DENY", "No applicable permission rule")
    decisions = {r.get("decision") for r in matched}
    if "DENY" in decisions or not decisions <= {"ALLOW", "REQUIRE_APPROVAL"}:
        return answer("DENY", "Explicit deny or invalid policy")
    rank = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}
    if sensitivity not in rank or any(rank[sensitivity] > rank.get(r.get("max_sensitivity", "PUBLIC"), -1) for r in matched):
        return answer("DENY", "Data sensitivity exceeds permission")
    if "REQUIRE_APPROVAL" in decisions:
        valid = any(a.get("action_hash") == action_hash and a.get("status") == "APPROVED" for a in approvals)
        if not valid:
            return answer("REQUIRE_APPROVAL", "Exact action approval required")
    return answer("ALLOW", "Explicit matching permission")
