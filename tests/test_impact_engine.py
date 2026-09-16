import pytest

from service.impact_engine import ImpactEngine

from models.contract import Contract
from service.contract_service import ContractService
from models.contract_models import BreakingChangeRequest, BreakingChange


def test_total_field_removal_impacts_billing():
    engine = ImpactEngine()
    
    # Arrange 
    breaking_changes = [BreakingChange(
        category="response-property-removed",
        severity="critical",
        message="Response field 'total' was removed",
        location="GET /orders/{id}"
    ), BreakingChange(
        category="response-property-removed",
        severity="high",
        message="Response field 'customer_name' was removed",
        location="GET /orders/{id}"
    )]
    # Act
    impact_res = engine.analyze_impact(contract_name_or_title="Order API", breaking_changes=breaking_changes)
    
    # Assert
    assert impact_res.has_impact == True
    assert any(c.consumer_name == "Billing" for c in impact_res.impacted_consumers if c)
    assert any(c.consumer_name == "Frontend" for c in impact_res.impacted_consumers if c)
    
def test_unknown_field_change_impacts_nobody():
    engine = ImpactEngine()

    breaking_changes = [BreakingChange(
        category="response-property-removed",
        severity="high",
        message="Response field 'consumer_name' was removed",  # no consumer depends on 'consumer_name'
        location="GET /orders/{id}"
    )]

    impact_res = engine.analyze_impact(contract_name_or_title="Order API",
                                       breaking_changes=breaking_changes)

    assert impact_res.has_impact is False
    assert impact_res.impacted_consumers == []
    
        
    
    
breaking_changes =[BreakingChange(
    category="response-property-removed",
    severity="high",
    message="consumer_name was changed to consumer",
    location="GET /orders/{id}"
)]


"""
impact_res = engine.analyze_impact(contract_name_or_title="Order API", breaking_changes=breaking_changes)
print("impact res: ", impact_res)

for consumer in impact_res.impacted_consumers:
    print("consumers impaced: ", consumer.consumer_name)
    print("Endpoints: ", consumer.endpoint)
    print(f"  └─ Dependent Field: {consumer.field}")
    print(f"  └─ Issue: {consumer.change_message}")
    
"""