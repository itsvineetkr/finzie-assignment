from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class IntentType(enum.Enum):
    FAQ = "faq"
    COMPLAINT = "complaint"
    ACCOUNT_INQUIRY = "account_inquiry"
    GENERAL = "general"

class TicketStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class NotificationStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text)
    intent = Column(Enum(IntentType))
    agent_type = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(String(20), default="medium")
    customer_email = Column(String(255))
    customer_phone = Column(String(20))
    session_id = Column(String(255), index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class FAQ(Base):
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100))
    keywords = Column(Text)  # JSON string of keywords
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String(255))
    recipient_phone = Column(String(20))
    message = Column(Text, nullable=False)
    notification_type = Column(String(50))  # email, sms, whatsapp
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    error_message = Column(Text)
    session_id = Column(String(255), index=True)
    ticket_id = Column(Integer, index=True)
    created_at = Column(DateTime, server_default=func.now())
    sent_at = Column(DateTime)
