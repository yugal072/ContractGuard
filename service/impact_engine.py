import re
from typing import List

from database.connection import SessionLocal
from models.contract import Contract
from models.contract_version import ContractVersion
from models.consumer_dependency import ConsumerDependency
from models.contract_models import BreakingChange, ImpactConsumerDetail, ConsumerImpactResponse

# Ensure model relationships are registered in SQLalchemy mapper
import models.contract
import models.contract_version
import models.consumer
import models.consumer_dependency

class ImpactEngine:
    def _normalize_path(self, path:str) -> str:
        """Lowercase, strip trailing slashes, and replace all dynamic braces {...} with {}."""
        path = path.strip().lower().rstrip("/")
        return re.sub(r"\{[^}]+\}", "{}", path)
    
    def _is_global_change(self, change: BreakingChange) -> bool:
        return change.category in {
            "api-removed-without-deprecation",
            "response-success-status-removed",
        }
    
    def analyze_impact(self, contract_name_or_title:str, breaking_changes: List[BreakingChange])->ConsumerImpactResponse:
        if not breaking_changes:
            return ConsumerImpactResponse(has_impact=False, impacted_consumers=[])
        
        db=SessionLocal()
        try:
            # 1 resolve DB contract by name or title
            contract = db.query(Contract).filter(Contract.name == contract_name_or_title).first()
            if not contract:
                raise ValueError(
                    f"Contract '{contract_name_or_title}' not found in database"
                )
            
            # 2 Fetch all dependencies across all versions of this contract
            dependencies = (
                db.query(ConsumerDependency)
                .join(ContractVersion)
                .filter(ContractVersion.contract_id == contract.id)
                .all()
            )
            
            impacted = []
            
            for change in breaking_changes:
                # Parse location (eg "GET /users")
                loc = change.location or ""
                parts = loc.split(" ",1)
                if len(parts) ==2:
                    change_method = parts[0].strip().upper()
                    change_path = self._normalize_path(parts[1])
                else:
                    change_method = ""
                    change_path = self._normalize_path(loc)
                    
                for dep in dependencies:
                    # Parse dep.endpoint (e.g., "GET /users/{id}")
                    dep_parts = dep.endpoint.split(" ", 1)
                    if len(dep_parts) == 2:
                        dep_method = dep_parts[0].strip().upper()
                        dep_path = self._normalize_path(dep_parts[1])
                    else:
                        dep_method = ""
                        dep_path = self._normalize_path(dep.endpoint)

                    # Step 1: Match Method + Path
                    method_matches = (not change_method) or (change_method == dep_method)
                    path_matches = (change_path == dep_path)
                    
                    if method_matches and path_matches:
                        # Step 2: Check global endpoint change vs precise field change
                        is_global_change = self._is_global_change(change)

                        field_matches = False
                        if not is_global_change and dep.field:
                            field_token = dep.field.strip().lower()
                            msg_lower = change.message.lower()
                            # Check if the consumer's registered field is mentioned in the change text
                            if field_token in msg_lower:
                                field_matches = True

                        if is_global_change or field_matches:
                            impacted.append(ImpactConsumerDetail(
                                consumer_name=dep.consumer.name,
                                type=dep.consumer.type,
                                criticality=dep.consumer.criticality,
                                endpoint=dep.endpoint,
                                field=dep.field,
                                usage_description=dep.usage_description,
                                change_category=change.category,
                                change_message=change.message
                            ))
                            
            # Deduplicate multiple hits
            unique_impacts = []
            seen=set()
            for detail in impacted:
                key = (detail.consumer_name, detail.endpoint, detail.field,detail.change_category)
                if key not in seen:
                    seen.add(key)
                    unique_impacts.append(detail)
            
            return ConsumerImpactResponse(
                has_impact=len(unique_impacts) > 0,
                impacted_consumers=unique_impacts
            )                
        finally:
            db.close()