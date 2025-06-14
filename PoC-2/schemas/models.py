from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class IntentType(str, Enum):
    FAQ = "faq"
    COMPLAINT = "complaint"
    ACCOUNT_INQUIRY = "account_inquiry"
    GENERAL = "general"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: IntentType
    agent_type: str
    session_id: str
    ticket_number: Optional[str] = None
    created_at: datetime


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    status: TicketStatus
    priority: str
    customer_email: Optional[str]
    customer_phone: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FAQResponse(BaseModel):
    id: int
    question: str
    answer: str
    category: Optional[str]

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    message: str
    notification_type: str = Field(..., pattern="^(email|sms|whatsapp)$")


class IntentClassificationResponse(BaseModel):
    intent: IntentType
    confidence: float
    reasoning: Optional[str] = None
