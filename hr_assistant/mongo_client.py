from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pymongo import MongoClient

from .config import Settings


@dataclass
class MongoCollections:
    employees: str
    promotion_rules: str
    promotion_progress: str


class MongoRepository:
    def __init__(self, settings: Settings, collections: Optional[MongoCollections] = None):
        self._client = MongoClient(settings.mongodb_uri)
        self._db = self._client[settings.mongodb_db]
        self._collections = collections or MongoCollections(
            employees=settings.mongodb_employees_collection,
            promotion_rules=settings.mongodb_promotion_rules_collection,
            promotion_progress=settings.mongodb_promotion_progress_collection,
        )

    def get_employee(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._db[self._collections.employees].find_one({"_id": user_id})

    def update_address(self, user_id: str, address: Dict[str, Any]) -> bool:
        res = self._db[self._collections.employees].update_one(
            {"_id": user_id},
            {"$set": {"address": address}},
        )
        return res.modified_count > 0

    def get_promotion_rule(self, role: str, target_level: str) -> Optional[Dict[str, Any]]:
        return self._db[self._collections.promotion_rules].find_one(
            {"role": role, "target_level": target_level}
        )

    def get_promotion_progress(self, user_id: str, target_level: str) -> Optional[Dict[str, Any]]:
        return self._db[self._collections.promotion_progress].find_one(
            {"user_id": user_id, "target_level": target_level}
        )
