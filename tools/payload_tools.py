from models.contract_models import PayloadValidationResponse, PayloadValidationRequest
from service.payload_validation_service import PayloadValidateService
from service.trial import mcp

@mcp.tool(
    title="Validate Payload",
    description="Validate a JSON payload against an OpenAPI request body schema",
)
async def contractguard_validate_payload(
    request: PayloadValidationRequest,
)-> PayloadValidationResponse:
    return PayloadValidateService().validate(request)