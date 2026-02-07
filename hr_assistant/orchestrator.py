from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .mongo_client import MongoRepository
from .promotion import build_promotion_response, infer_target_level
from .rag import RagService
from .router import route_message
from .workflows import (
    UpdateAddressState,
    parse_address_fields,
    update_address_next_prompt,
)


@dataclass
class ChatResponse:
    text: str
    route: str
    debug: Optional[Dict[str, Any]] = None


class Orchestrator:
    def __init__(self, rag: RagService, repo: Optional[MongoRepository] = None):
        self._rag = rag
        self._repo = repo or MongoRepository(rag._settings)
        self._workflow_state: Dict[str, UpdateAddressState] = {}

    def handle(self, *, user_id: str, text: str, user_context: Optional[Dict[str, Any]] = None) -> ChatResponse:
        user_context = user_context or {}
        # If we are mid-workflow for this user, keep routing to the address flow.
        if user_id in self._workflow_state:
            r = route_message("update address", user_context)
        else:
            r = route_message(text, user_context)

        if r.route == "updateAddress":
            state = self._workflow_state.get(user_id) or UpdateAddressState()

            if text.strip().lower() in {"cancel", "stop", "exit"}:
                self._workflow_state.pop(user_id, None)
                return ChatResponse(
                    text="Address update cancelled. How can I help you next?",
                    route="updateAddress",
                )

            if text.strip().lower() == "confirm":
                # Must have all fields first
                missing_prompt = update_address_next_prompt(state)
                if "please provide" in missing_prompt.lower():
                    return ChatResponse(text=missing_prompt, route="updateAddress")

                address = {
                    "line1": state.address_line1 or "",
                    "line2": state.address_line2 or "",
                    "city": state.city or "",
                    "state": state.state or "",
                    "postal_code": state.postal_code or "",
                    "country": state.country or "",
                }
                updated = self._repo.update_address(user_id=user_id, address=address)
                self._workflow_state.pop(user_id, None)
                if updated:
                    return ChatResponse(text="Done — I updated your address.", route="updateAddress")
                return ChatResponse(text="I couldn't find your profile to update.", route="updateAddress")

            # Otherwise parse any supplied fields and prompt next step
            state = parse_address_fields(text, state)
            prompt = update_address_next_prompt(state)
            if "Please confirm" in prompt:
                state.awaiting_confirmation = True
            self._workflow_state[user_id] = state
            return ChatResponse(text=prompt, route="updateAddress")

        if r.route == "promotion":
            employee = self._repo.get_employee(user_id)
            if not employee:
                return ChatResponse(
                    text="I couldn't find your employee profile. Please check your user ID.",
                    route="promotion",
                )
            target_level = infer_target_level(employee)
            rule = self._repo.get_promotion_rule(employee.get("role", ""), target_level)
            progress = self._repo.get_promotion_progress(user_id, target_level)
            if not rule or not progress:
                return ChatResponse(
                    text=(
                        "I couldn't find promotion criteria or your progress data. "
                        "Please ask HR to add your promotion rule or progress record."
                    ),
                    route="promotion",
                )
            summary = build_promotion_response(employee, rule, progress)
            return ChatResponse(text=summary, route="promotion")

        # Default: policy RAG
        ans = self._rag.answer_policy_question(question=text, user_context=user_context)
        return ChatResponse(text=ans.answer, route="policyRag")

