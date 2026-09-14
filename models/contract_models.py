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
  
class ImpactConsumerDetail(BaseModel):
    consumer_name: str
    type:str
    criticality:str
    endpoint:str
    field:str 
    usage_description: Optional[str]=None
    change_category:str 
    change_message:str 
      
class BreakingChangeResponse(BaseModel):
    breaking: bool
    changes: list[BreakingChange]
    summary: BreakingSummary
    diff: Optional[dict] = None
    impacted_consumers: list[ImpactConsumerDetail] = Field(default_factory=list)
    
class ConsumerImpactResponse(BaseModel):
    has_impact:bool
    impacted_consumers:list[ImpactConsumerDetail]