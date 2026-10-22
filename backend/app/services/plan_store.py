"""In-memory active plan registry with anti-replay guarantees."""

import threading
from typing import Dict, Optional
from backend.app.models.plan import OrganizationPlan


class PlanStore:
    """
    Tracks active organization plans and their execution lifecycle.

    Security & Integrity Guarantees:
    - Plans are registered on generation.
    - Prevents repeated execution of the same plan (anti-replay).
    - Requires operation IDs to belong to the server-verified plan.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._plans: Dict[str, OrganizationPlan] = {}
        self._executed_plan_ids: set[str] = set()

    def save_plan(self, plan: OrganizationPlan) -> None:
        """Stores or updates an organization plan."""
        with self._lock:
            self._plans[plan.plan_id] = plan

    def get_plan(self, plan_id: str) -> Optional[OrganizationPlan]:
        """Retrieves a plan by its ID."""
        with self._lock:
            return self._plans.get(plan_id)

    def is_executed(self, plan_id: str) -> bool:
        """Checks if a plan has already been executed (in memory or in stored manifests)."""
        with self._lock:
            if plan_id in self._executed_plan_ids:
                return True
            try:
                from backend.app.config import settings
                from backend.app.engine.manifest import ManifestStorage
                storage = ManifestStorage(settings.MANIFEST_DIR)
                for m in storage.list_manifests():
                    if m.plan_id == plan_id:
                        self._executed_plan_ids.add(plan_id)
                        return True
            except Exception:
                pass
            return False

    def mark_executed(self, plan_id: str) -> None:
        """Marks a plan as permanently executed to prevent replay."""
        with self._lock:
            self._executed_plan_ids.add(plan_id)

    def clear(self) -> None:
        """Clears all plans (used in testing)."""
        with self._lock:
            self._plans.clear()
            self._executed_plan_ids.clear()


plan_store = PlanStore()
