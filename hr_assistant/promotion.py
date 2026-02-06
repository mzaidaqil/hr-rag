from __future__ import annotations

from typing import Any, Dict, Tuple


_RATING_ORDER = ["Below", "Meets", "Exceeds"]


def _rating_meets(required: str, actual: str) -> bool:
    if required not in _RATING_ORDER or actual not in _RATING_ORDER:
        return False
    return _RATING_ORDER.index(actual) >= _RATING_ORDER.index(required)


def _next_level(current_level: str) -> str:
    # Simple fallback if you store levels like L1/L2/L3
    if current_level.startswith("L") and current_level[1:].isdigit():
        return f"L{int(current_level[1:]) + 1}"
    return current_level


def build_promotion_response(
    employee: Dict[str, Any],
    rule: Dict[str, Any],
    progress: Dict[str, Any],
) -> str:
    missing = []

    months_needed = int(rule.get("min_months_in_level", 0))
    months_have = int(progress.get("months_in_level", 0))
    if months_have < months_needed:
        missing.append(f"- Months in level: {months_have}/{months_needed}")

    required_rating = str(rule.get("required_performance_rating", "Meets"))
    actual_rating = str(progress.get("last_rating", ""))
    if not _rating_meets(required_rating, actual_rating):
        missing.append(f"- Performance rating: {actual_rating} (needs {required_rating})")

    required_projects = int(rule.get("required_projects", 0))
    projects_done = int(progress.get("projects_completed", 0))
    if projects_done < required_projects:
        missing.append(f"- Projects: {projects_done}/{required_projects}")

    required_score = int(rule.get("required_competency_score", 0))
    actual_score = int(progress.get("competency_score", 0))
    if actual_score < required_score:
        missing.append(f"- Competency score: {actual_score}/{required_score}")

    criteria = (
        "Promotion criteria:\n"
        f"- Minimum months in level: {months_needed}\n"
        f"- Performance rating: {required_rating}\n"
        f"- Projects completed: {required_projects}\n"
        f"- Competency score: {required_score}\n"
    )

    progress_block = (
        "Your current progress:\n"
        f"- Months in level: {months_have}\n"
        f"- Performance rating: {actual_rating}\n"
        f"- Projects completed: {projects_done}\n"
        f"- Competency score: {actual_score}\n"
    )

    if missing:
        missing_block = "Still needed:\n" + "\n".join(missing)
        return f"{criteria}\n{progress_block}\n{missing_block}"

    return f"{criteria}\n{progress_block}\nYou appear eligible to proceed with a promotion request."


def infer_target_level(employee: Dict[str, Any]) -> str:
    return _next_level(str(employee.get("level", "")))
