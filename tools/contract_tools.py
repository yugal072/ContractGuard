from models.contract_models import BreakingChangeRequest, BreakingChangeResponse, ConsumerImpactResponse
from service.contract_service import ContractService
from service.trial import mcp
from service.baseline_resolver import BaselineResolver
from service.spec_resolver import SpecResolver

import yaml
import asyncio
from pydantic import BaseModel, Field
from typing import Optional, Literal

class CheckContractBreakingChangesRequest(BaseModel):
    contract: str = Field(..., description="FastAPI module path (e.g. 'resource.api.main.app') of DB contract name (e.g. 'Order API)")
    version: Optional[str] = Field(None, description="Optional PostgreSQL version to match exactly")
    baseline: Optional[str] = Field("main", description="Optional Git baseline reference")
    mode: Literal["breaking", "diff"] = Field("breaking", description="Comparision mode: 'breaking' or 'diff' ")
    
class ConsumerImpactRequest(BaseModel):
    contract: str = Field(..., description="FastAPI module path or DB contract name")
    version: Optional[str] = Field(None, description="Optional PostgreSQL version")
    baseline: Optional[str] = Field("main", description="Optional Git baseline reference")
    mode: Literal["breaking", "diff"] = Field("breaking", description="Comparison mode: 'breaking' or 'diff'")
    
@mcp.tool(title="Check Contract Breaking Changes", description="Check breaking changes in a contract by automatically resolving its baseline and current specs")
async def contractguard_breaking_changes(request: CheckContractBreakingChangesRequest) -> BreakingChangeResponse:
    # 1. resolve specs
    spec_resolver = SpecResolver()
    new_spec = spec_resolver.resolve(request.contract)
    if not new_spec:
        raise ValueError(f"Could not resolve current spec for contract: {request.contract}")
    
    # Resolve baesline spec from git or db
    baseline_resolver = BaselineResolver()
    old_spec = baseline_resolver.resolve(
        contract=request.contract,
        version=request.version,
        baseline=request.baseline
    )
    if not old_spec:
        raise ValueError(f"Could not resolve current spec for contract: {request.contract}")
    
    # 2. Extract OpenAPI Title to identify matching DB Contract
    try:
        spec_dict= yaml.safe_load(new_spec)
        contract_title = spec_dict.get("info", {}).get("title", request.contract)
    except Exception:
        contract_title = request.contract
    
    # 3 Pipeline Execution (Feed the specs into ContractService)
    breaking_request = BreakingChangeRequest(old_spec=old_spec, new_spec=new_spec)
    contract_service = ContractService()
    
    return await asyncio.to_thread(contract_service.check_breaking_changes, 
                                   breaking_request,
                                   contract_title,
                                   request.mode)


# The consumer Impact Tool
@mcp.tool(title="Check Consumer Impact", description="Identify consumers impacted by breaking changes in a contract")
async def contractguard_consumer_impact(request: ConsumerImpactRequest) -> ConsumerImpactResponse:
    # 1. Resolve specs
    spec_resolver = SpecResolver()
    new_spec = spec_resolver.resolve(request.contract)
    if not new_spec:
        raise ValueError(f"Could not resolve current spec: {request.contract}")
    
    baseline_resolver = BaselineResolver()
    old_spec = baseline_resolver.resolve(
        contract=request.contract,
        version=request.version,
        baseline=request.baseline
    )
    if not old_spec:
        raise ValueError(f"Could not resolve baseline spec: {request.contract}")
          
    # 3. Extract OpenAPI title to map to DB contract
    try:
        spec_dict = yaml.safe_load(new_spec)
        contract_title = spec_dict.get("info", {}).get("title", request.contract)
    except Exception:
        contract_title = request.contract
        
    # 3. Detect breaking changes + consumer impact
    breaking_request = BreakingChangeRequest(
        old_spec=old_spec,
        new_spec=new_spec
    )
    
    contract_service = ContractService()
    
    res = await asyncio.to_thread(
        contract_service.check_breaking_changes,
        breaking_request,
        contract_title,
        request.mode
    )
    
    # 4. Return consumer impact already calculated
    return ConsumerImpactResponse(
        has_impact=len(res.impacted_consumers) > 0,
        impacted_consumers=res.impacted_consumers
    )