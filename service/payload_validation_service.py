import json 
import yaml 

from jsonschema import Draft7Validator

from models.contract_models import (
    PayloadValidationRequest,
    PayloadValidationResponse,
    ValidationErrorDetail,
)

class PayloadValidateService:
    """Validate a JSON payload against an OpenAPI request-body schema.
    
    MVP limitations (deliberate):
    - no $ref / conponents.schemas resolution 
    - no content-type negotiation (application/json only)
    - request-body validation only (no-response)
    """
    
    def validate(self, request: PayloadValidationRequest)-> PayloadValidationResponse:
        # 1 parse spec (same parse style as contractservice)
        try:
            spec = json.loads(request.spec)
        except json.JSONDecodeError:
            try:
                spec = yaml.safe_load(request.spec)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid spec format: {e}")
            
        # 2. Find operation
        try:
            operation = spec["paths"][request.path][request.method.lower()]
        except (KeyError, TypeError):
            raise ValueError(
                f"No operation '{request.method.upper()} {request.path}' in spec"
            )

        # 3. Extract JSON request body schema
        schema = (
            (operation.get("requestBody") or {})
            .get("content",{})
            .get("application/json", {})
            .get("schema")
        )
        if schema is None:
            raise ValueError("No JSON request body schema")

        # 4. Validate
        validator= Draft7Validator(schema)
        errors= sorted(
            validator.iter_errors(request.payload),
            key=lambda error: list(error.absolute_path),
        )
        
        # 5. Normalize + return
        return PayloadValidationResponse(
            valid= not errors,
            errors=[
                ValidationErrorDetail(
                    field=".".join(str(part) for part in error.absolute_path),
                    message=error.message,
                )
                for error in errors
            ],
        )