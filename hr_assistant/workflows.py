from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Optional


@dataclass
class UpdateAddressState:
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    awaiting_confirmation: bool = False


def _missing_fields(s: UpdateAddressState) -> list[str]:
    missing = []
    if not s.address_line1:
        missing.append("address_line1")
    if not s.city:
        missing.append("city")
    if not s.state:
        missing.append("state")
    if not s.postal_code:
        missing.append("postal_code")
    if not s.country:
        missing.append("country")
    return missing


def update_address_next_prompt(state: UpdateAddressState) -> str:
    missing = _missing_fields(state)
    if missing:
        return (
            "To update your address, please provide: "
            + ", ".join(missing)
            + ".\n"
            "Example format:\n"
            "address_line1: 12 Main St\n"
            "address_line2: Apt 3 (optional)\n"
            "city: Boston\n"
            "state: MA\n"
            "postal_code: 02110\n"
            "country: US"
        )
    if not state.awaiting_confirmation:
        return (
            "Please confirm I should update your address to:\n"
            f"- address_line1: {state.address_line1}\n"
            f"- address_line2: {state.address_line2 or ''}\n"
            f"- city: {state.city}\n"
            f"- state: {state.state}\n"
            f"- postal_code: {state.postal_code}\n"
            f"- country: {state.country}\n\n"
            "Reply `confirm` to submit, `cancel` to stop, or reply with corrections."
        )
    return "Reply `confirm` to submit, `cancel` to stop, or reply with corrections."


def parse_address_fields(text: str, state: UpdateAddressState) -> UpdateAddressState:
    # Very basic key:value parser
    kv: Dict[str, str] = {}

    lines = [ln.strip() for ln in (text or "").splitlines() if ":" in ln]
    for ln in lines:
        k, v = ln.split(":", 1)
        kv[k.strip().lower()] = v.strip()

    # Also support single-line inputs with multiple key:value pairs.
    pattern = re.compile(
        r"\b(address_line1|address_line2|city|state|postal_code|country)\s*:\s*(.+?)(?=\s+\b(?:address_line1|address_line2|city|state|postal_code|country)\b\s*:|$)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text or ""):
        key = match.group(1).lower()
        value = match.group(2).strip()
        if value:
            kv[key] = value

    if "address_line1" in kv:
        state.address_line1 = kv["address_line1"]
    if "address_line2" in kv:
        state.address_line2 = kv["address_line2"]
    if "city" in kv:
        state.city = kv["city"]
    if "state" in kv:
        state.state = kv["state"]
    if "postal_code" in kv:
        state.postal_code = kv["postal_code"]
    if "country" in kv:
        state.country = kv["country"]

    return state

