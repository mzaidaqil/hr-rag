from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RouteResult:
    route: str  # "policyRag" | "updateAddress" | "promotion"
    confidence: float


def route_message(text: str, user_context: Optional[Dict[str, Any]] = None) -> RouteResult:
    t = (text or "").lower().strip()

    # Very simple rule router for Phase 1; can be replaced by an LLM classifier later.
    if re.search(r"\b(promotion|promote|eligible)\b", t):
        return RouteResult(route="promotion", confidence=0.9)

    # Route to address flow if user mentions address or provides address fields.
    if re.search(r"\b(update|change)\b.*\b(address|home address|adress)\b", t) or re.search(
        r"\bmy address\b", t
    ):
        return RouteResult(route="updateAddress", confidence=0.9)

    if re.search(r"\baddress_line1\b|\baddress_line2\b|\bpostal_code\b|\bcountry\b|\bcity\b|\bstate\b", t):
        return RouteResult(route="updateAddress", confidence=0.9)

    return RouteResult(route="policyRag", confidence=0.6)

