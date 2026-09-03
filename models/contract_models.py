from typing import Optional
from pydantic import BaseModel, Field

class BreakingChangeRequest(BaseModel):
    old_spec: str= Field(min_length =20)
    new_spec: str = Field(min_length=20)
    
class BreakingChange(BaseModel):
    category: str
    severity: str
    message: str
    location: Optional[str]
    
class BreakingSummary(BaseModel):
    total_changes: int
    critical: int
    high:int
    low: int
    
class BreakingChangeResponse(BaseModel):
    breaking: bool
    changes: list[BreakingChange]
    summary: BreakingSummary