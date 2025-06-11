from pydantic import BaseModel
from typing import Optional


class MakeCallRequest(BaseModel):
    phone_number: str
    assistant_id: Optional[str] = None
    first_message: Optional[str] = None
    purpose: Optional[str] = "Customer outreach"

class CallResponse(BaseModel):
    status: str
    call_id: Optional[str] = None
    message: str