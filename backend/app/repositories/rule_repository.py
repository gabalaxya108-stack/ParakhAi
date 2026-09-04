import os
import json
import glob
from typing import List, Optional, Dict
from backend.app.schemas.rules import RuleModel
from backend.app.core.logging import get_logger

logger = get_logger("repositories.rules")

class RuleRepository:
    """
    Deterministic rule repository supporting version selection,
    category applicability filtering, and statutory source citation.
    """

    def __init__(self, rules_dir: str = None):
        self.rules_dir = rules_dir or os.path.join(os.getcwd(), "rules")
        self._cache: Dict[str, Dict[str, RuleModel]] = {}  # version -> {rule_id: RuleModel}
        self.reload_rules()

    def reload_rules(self):
        """Scans the /rules directory and loads all versioned JSON catalogs."""
        self._cache.clear()
        json_files = glob.glob(os.path.join(self.rules_dir, "rules_*.json"))
        
        for fpath in json_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        rule = RuleModel(**item)
                        ver = rule.rule_version
                        if ver not in self._cache:
                            self._cache[ver] = {}
                        self._cache[ver][rule.rule_id] = rule
            except Exception as e:
                logger.error(f"Failed to load rule catalog file '{fpath}': {e}")

        logger.info(f"Loaded {sum(len(v) for v in self._cache.values())} rules across versions: {list(self._cache.keys())}")

    def get_available_versions(self) -> List[str]:
        return sorted(list(self._cache.keys()), reverse=True)

    def get_latest_version(self) -> str:
        versions = self.get_available_versions()
        return versions[0] if versions else "2026.1"

    def list_rules(
        self,
        version: Optional[str] = None,
        category: Optional[str] = None,
        field: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[RuleModel]:
        target_version = version or self.get_latest_version()
        rules_map = self._cache.get(target_version, {})
        results = []

        for rule in rules_map.values():
            # 1. Enabled filter
            if enabled_only and not rule.enabled:
                continue

            # 2. Applicability filtering: matches category or applicable to 'all'
            if category:
                cat_lower = category.lower().strip()
                rule_cats = [c.lower().strip() for c in rule.applicable_product_categories]
                if "all" not in rule_cats and cat_lower not in rule_cats:
                    continue

            # 3. Field filter
            if field:
                if rule.field_to_validate.lower() != field.lower().strip():
                    continue

            results.append(rule)

        # Sort by severity priority (CRITICAL -> HIGH -> MEDIUM -> LOW) then rule_id
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        results.sort(key=lambda r: (severity_order.get(r.severity, 99), r.rule_id))
        return results

    def get_rule(self, rule_id: str, version: Optional[str] = None) -> Optional[RuleModel]:
        target_version = version or self.get_latest_version()
        rules_map = self._cache.get(target_version, {})
        return rules_map.get(rule_id)

_rule_repo_instance = None

def get_rule_repository() -> RuleRepository:
    global _rule_repo_instance
    if _rule_repo_instance is None:
        _rule_repo_instance = RuleRepository()
    return _rule_repo_instance
