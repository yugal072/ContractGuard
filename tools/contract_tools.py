from models.contract_models import BreakingChangeRequest
from service.contract_service import ContractService
from service.trial import mcp
import asyncio

@mcp.tool(title="Check Breaking Changes", description="Check breaking Changes in a API contract")
async def breaking_changes(request: BreakingChangeRequest):
    service = ContractService()
    return await asyncio.to_thread(service.check_breaking_changes, request)