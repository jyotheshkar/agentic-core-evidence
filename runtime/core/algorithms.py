"""Transparent deterministic heuristics, not calibrated probabilities or optimality claims."""
from __future__ import annotations
import copy
from .contracts import CoreError, validate, EVIDENCE_SCHEMA


def route_capabilities(required: list[str] | dict[str, float], candidates: list[dict], *, context_budget: int = 12000, available_tools=(), minimum_trust: int = 2) -> dict:
    weights = required if isinstance(required, dict) else {r: 1.0 for r in required}
    if any(not isinstance(w, (int, float)) or w <= 0 for w in weights.values()):
        raise CoreError("Capability weights must be positive")
    by_id = {c["id"]: c for c in candidates}
    if len(by_id) != len(candidates):
        raise CoreError("Duplicate candidate IDs")
    excluded, closures = {}, {}
    def closure(cid, trail=()):
        if cid in trail:
            raise CoreError("Dependency cycle")
        if cid not in by_id:
            raise CoreError("Missing dependency " + cid)
        c = by_id[cid]
        if not c.get("available", False):
            raise CoreError("Unavailable")
        if c.get("trust", 0) < minimum_trust:
            raise CoreError("Insufficient reviewed trust")
        if not c.get("compatible", True):
            raise CoreError("Incompatible host")
        if not set(c.get("required_tools", [])) <= set(available_tools):
            raise CoreError("Unavailable required tool")
        if c.get("context_tokens", 0) < 0 or c.get("activation_cost", 1) <= 0:
            raise CoreError("Invalid candidate cost")
        result = {cid}
        for dep in c.get("dependencies", []):
            result |= closure(dep, (*trail, cid))
        for item in result:
            if set(by_id[item].get("conflicts", [])) & result:
                raise CoreError("Conflicting dependency closure")
        return result
    for cid in sorted(by_id):
        try:
            closures[cid] = closure(cid)
        except CoreError as exc:
            excluded[cid] = str(exc)
    chosen, covered, rationale = set(), set(), []
    while set(weights) - covered:
        options = []
        for cid, cl in closures.items():
            add = cl - chosen
            if not add:
                continue
            union = chosen | cl
            if any(set(by_id[s].get("conflicts", [])) & union for s in union):
                excluded[cid] = "Conflict with selected capability"
                continue
            if sum(by_id[s].get("context_tokens", 0) for s in union) > context_budget:
                excluded[cid] = "Context budget exceeded"
                continue
            marginal = (set().union(*(set(by_id[s].get("capabilities", [])) for s in add)) & set(weights)) - covered
            gain = sum(weights[s] for s in marginal)
            cost = sum(by_id[s].get("activation_cost", 1) for s in add)
            if gain:
                options.append((-(gain / cost), cost, cid, add, marginal))
        if not options:
            break
        score, cost, cid, add, marginal = sorted(options, key=lambda x: x[:3])[0]
        chosen |= add
        covered |= marginal
        rationale.append({"candidate": cid, "dependency_closure_added": sorted(add), "marginal_coverage": sorted(marginal), "activation_cost": cost, "weighted_gain_per_cost": -score})
    return {"algorithm": "deterministic greedy weighted set cover; not globally optimal", "selected": sorted(chosen),
        "uncovered": sorted(set(weights) - covered), "excluded": [{"id": k, "reason": v} for k, v in sorted(excluded.items())], "rationale": rationale,
        "context_tokens": sum(by_id[s].get("context_tokens", 0) for s in chosen),
        "coverage_matrix": {r: {c: int(r in by_id[c].get("capabilities", [])) for c in sorted(by_id)} for r in weights}}


def keyword_baseline(required: list[str], candidates: list[dict]) -> list[str]:
    """Deliberately simple labelled routing comparator; it does not confer authority."""
    text = " ".join(required).lower()
    return sorted(c["id"] for c in candidates if any(tag.lower() in text for tag in c.get("tags", c.get("capabilities", []))))


def evaluate_options(options: list[dict], criteria: list[dict], *, perturbation: float = 0.2) -> dict:
    feasible = [o for o in options if o.get("feasible", True)]
    if not feasible:
        return {"recommendation": None, "reason": "No feasible options", "ranking": [], "unstable": False}
    if not criteria or not 0 <= perturbation <= 1:
        raise CoreError("Criteria and bounded sensitivity perturbation required")
    for c in criteria:
        if c["direction"] not in {"max", "min"} or c["max"] <= c["min"] or c["weight"] < 0 or not c.get("unit"):
            raise CoreError("Invalid utility criterion")
    if sum(c["weight"] for c in criteria) <= 0:
        raise CoreError("Positive total weight required")
    def rank(cs):
        total = sum(c["weight"] for c in cs)
        values = []
        for option in feasible:
            score, parts = 0.0, {}
            for c in cs:
                raw = option["values"][c["id"]]
                if not isinstance(raw, (int, float)) or not c["min"] <= raw <= c["max"]:
                    raise CoreError("Option outside declared criterion range")
                norm = (raw - c["min"]) / (c["max"] - c["min"])
                if c["direction"] == "min":
                    norm = 1 - norm
                parts[c["id"]] = norm
                score += norm * c["weight"] / total
            values.append({"id": option["id"], "utility": score, "normalised": parts})
        return sorted(values, key=lambda row: (-row["utility"], row["id"]))
    ranking, variants = rank(criteria), []
    for index, c in enumerate(criteria):
        for factor in [1 - perturbation, 1 + perturbation]:
            altered = copy.deepcopy(criteria)
            altered[index]["weight"] *= factor
            if sum(x["weight"] for x in altered) > 0:
                variants.append({"criterion": c["id"], "factor": factor, "winner": rank(altered)[0]["id"]})
    return {"recommendation": ranking[0]["id"], "ranking": ranking, "criteria": criteria, "sensitivity": variants,
        "unstable": any(v["winner"] != ranking[0]["id"] for v in variants), "choice_exists": len(feasible) > 1,
        "excluded": [o["id"] for o in options if not o.get("feasible", True)], "method": "weighted normalised utility; one-at-a-time sensitivity, not exhaustive uncertainty analysis"}


def assess_risk(likelihood: int, impact: int, reversibility: str, sensitivity: str, mitigations: list[str]) -> dict:
    if likelihood not in range(1, 6) or impact not in range(1, 6) or reversibility not in {"REVERSIBLE", "IRREVERSIBLE", "UNKNOWN"} or sensitivity not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
        raise CoreError("Invalid ordinal risk input")
    score = likelihood * impact
    escalation = score >= 12 or reversibility != "REVERSIBLE" or sensitivity in {"CONFIDENTIAL", "RESTRICTED"}
    return {"method": "ordinal heuristic, not probability", "likelihood": likelihood, "impact": impact, "score": score, "reversibility": reversibility,
        "data_sensitivity": sensitivity, "mitigations": mitigations, "requires_escalation": escalation, "stop_conditions": ["Guardian DENY", "missing authority", "unresolved contradictory evidence"]}


def assess_evidence(records: list[dict]) -> dict:
    for r in records:
        validate(r, EVIDENCE_SCHEMA)
    groups = {r["independence_group"] for r in records}
    direct = {r["independence_group"] for r in records if r["directness"] == "DIRECT"}
    contradictions = sorted({s for r in records for s in r["contradictions"]})
    missing = sorted({s for r in records for s in r["missing_information"]})
    return {"records": len(records), "independent_groups": len(groups), "direct_groups": len(direct), "contradictions": contradictions, "missing_information": missing,
        "strength": "MISSING" if not records else "CONTESTED" if contradictions else "DIRECT" if direct else "INDIRECT_OR_MODEL", "calibrated_probability": None}
