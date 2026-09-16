from models.contract_models import PayloadValidationRequest
from service.payload_validation_service import PayloadValidateService

SPEC = """ 
openapi: 3.0.0
info:
  title: Order API
  version: "1.0"
paths:
  /orders:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - customer_name
                - total
              properties:
                customer_name:
                  type: string
                total:
                  type: number
      responses:
        "200":
          description: Success
"""

def validate(payload):
    request = PayloadValidationRequest(
        spec=SPEC, path="/orders", method="POST", payload=payload
    )
    return PayloadValidateService().validate(request)

def test_validate_payload():
    res = validate({"customer_name": "Yugal", "total":500})
    assert res.valid is True
    assert res.errors ==[]
    
def test_invalid_payload():
    res= validate({"customer_name": 123, "total":"five hundred"})
    assert res.valid is False
    
    by_field= {e.field: e.message for e in res.errors}
    assert "customer_name" in by_field
    assert "type" in by_field["customer_name"]
    
    assert "total" in by_field
    assert "type" in by_field["total"]