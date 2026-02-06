from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EmployeeProfile:
    user_id: str
    full_name: str
    region: str = "US"
    address_line1: str = "123 Old St"
    address_line2: str = ""
    city: str = "Oldtown"
    state: str = "CA"
    postal_code: str = "90001"
    country: str = "US"


class MockHRIS:
    """In-memory mock HRIS (Phase 1)."""

    def __init__(self):
        self._employees: Dict[str, EmployeeProfile] = {}

    def get_employee(self, user_id: str) -> EmployeeProfile:
        if user_id not in self._employees:
            self._employees[user_id] = EmployeeProfile(
                user_id=user_id, full_name=f"Employee {user_id}"
            )
        return self._employees[user_id]

    def update_address(
        self,
        *,
        user_id: str,
        address_line1: str,
        address_line2: str,
        city: str,
        state: str,
        postal_code: str,
        country: str,
    ) -> EmployeeProfile:
        emp = self.get_employee(user_id)
        emp.address_line1 = address_line1
        emp.address_line2 = address_line2
        emp.city = city
        emp.state = state
        emp.postal_code = postal_code
        emp.country = country
        return emp

