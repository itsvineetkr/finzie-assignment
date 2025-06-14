from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
import logging
import uuid
from datetime import datetime

# Import our modules
from database.connection import get_db, init_db
from schemas.models import ChatRequest, ChatResponse, IntentClassificationResponse
from agents.intent_classifier import IntentClassifierAgent
from agents.routing_agent import RoutingAgent
from agents.support_agents import FAQAgent, TicketAgent, AccountAgent
from agents.notify_agent import NotifyAgent
from models.database import ChatMessage, FAQ
from utils.helpers import setup_logging, generate_session_id
from utils.prompts import *


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting AI Multi-Agent Chat Support System")
    await init_db()
    await populate_sample_faqs()
    yield
    # Shutdown
    logger.info("Shutting down AI Multi-Agent Chat Support System")


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


async def get_agents(db: AsyncSession = Depends(get_db)):
    """Get all agents with database session"""
    return {
        "intent_classifier": IntentClassifierAgent(),
        "router": RoutingAgent(),
        "faq_agent": FAQAgent(db),
        "ticket_agent": TicketAgent(db),
        "account_agent": AccountAgent(db),
        "notify_agent": NotifyAgent(db),
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """The main chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    agents: dict = Depends(get_agents),
):
    """Main chat endpoint that processes user messages through the agent pipeline"""
    try:
        session_id = chat_request.session_id or generate_session_id()

        logger.info(f"Processing chat request - Session: {session_id}")

        intent_result = await agents["intent_classifier"].process(chat_request.message)
        intent = intent_result["intent"]

        routing_context = {"intent": intent}
        routing_result = await agents["router"].process(
            chat_request.message, routing_context
        )
        target_agent_name = routing_result["target_agent"]

        support_context = {
            "intent": intent,
            "session_id": session_id,
            "customer_email": chat_request.customer_email,
            "customer_phone": chat_request.customer_phone,
        }

        agent_map = {
            "FAQAgent": agents["faq_agent"],
            "TicketAgent": agents["ticket_agent"],
            "AccountAgent": agents["account_agent"],
        }

        support_agent = agent_map.get(target_agent_name, agents["faq_agent"])
        agent_result = await support_agent.process(
            chat_request.message, support_context
        )

        if agent_result.get("requires_notification") and (
            chat_request.customer_email or chat_request.customer_phone
        ):
            notification_context = {
                "recipient_email": chat_request.customer_email,
                "recipient_phone": chat_request.customer_phone,
                "notification_type": "email" if chat_request.customer_email else "sms",
                "session_id": session_id,
                "ticket_number": agent_result.get("ticket_number"),
                "ticket_id": agent_result.get("ticket_id"),
            }

            notification_message = f"Your support request has been received. {agent_result.get('response', '')}"
            await agents["notify_agent"].process(
                notification_message, notification_context
            )

        chat_message = ChatMessage(
            session_id=session_id,
            user_message=chat_request.message,
            bot_response=agent_result["response"],
            intent=intent,
            agent_type=target_agent_name,
        )
        db.add(chat_message)
        await db.commit()

        return ChatResponse(
            response=agent_result["response"],
            intent=intent,
            agent_type=target_agent_name,
            session_id=session_id,
            ticket_number=agent_result.get("ticket_number"),
            created_at=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/classify-intent", response_model=IntentClassificationResponse)
async def classify_intent(
    chat_request: ChatRequest, agents: dict = Depends(get_agents)
):
    """Endpoint to test intent classification"""
    try:
        result = await agents["intent_classifier"].process(chat_request.message)

        return IntentClassificationResponse(
            intent=result["intent"],
            confidence=result["confidence"],
            reasoning=result.get("reasoning"),
        )

    except Exception as e:
        logger.error(f"Error in intent classification: {e}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")


@app.get("/api/agent-status")
async def agent_status(agents: dict = Depends(get_agents)):
    """Get status of all agents and their capabilities"""
    try:
        notify_capabilities = agents["notify_agent"].get_notification_capabilities()

        openai_available = agents["intent_classifier"].use_openai

        return {
            "agents": {
                "intent_classifier": {
                    "status": "active",
                    "openai_enabled": openai_available,
                },
                "router": {"status": "active"},
                "faq_agent": {"status": "active"},
                "ticket_agent": {"status": "active"},
                "account_agent": {"status": "active"},
                "notify_agent": {
                    "status": "active",
                    "capabilities": notify_capabilities,
                },
            },
            "system_status": "operational",
        }

    except Exception as e:
        logger.error(f"Error checking agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check error: {str(e)}")


@app.get("/api/chat-history/{session_id}")
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get chat history for a session"""
    try:

        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        return {
            "session_id": session_id,
            "messages": [
                {
                    "id": msg.id,
                    "user_message": msg.user_message,
                    "bot_response": msg.bot_response,
                    "intent": msg.intent.value if msg.intent else None,
                    "agent_type": msg.agent_type,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=f"History fetch error: {str(e)}")


async def populate_sample_faqs():
    """Populate the database with sample FAQs"""
    try:
        from database.connection import AsyncSessionLocal

        async with AsyncSessionLocal() as db:

            stmt = select(FAQ)
            result = await db.execute(stmt)
            existing_faqs = result.scalars().all()

            if len(existing_faqs) > 0:
                logger.info("FAQs already exist, skipping population")
                return

            # Sample FAQs
            sample_faqs = [
                {
                    "question": "How do I reset my password?",
                    "answer": "To reset your password, go to the login page and click 'Forgot Password'. Enter your email address and follow the instructions sent to your email.",
                    "category": "Account",
                    "keywords": '["password", "reset", "login", "forgot"]',
                },
                {
                    "question": "What are your business hours?",
                    "answer": "Our business hours are Monday to Friday, 9 AM to 6 PM EST. Our support team is available during these hours to assist you.",
                    "category": "General",
                    "keywords": '["hours", "business", "time", "support", "open"]',
                },
                {
                    "question": "How do I cancel my subscription?",
                    "answer": "To cancel your subscription, log into your account, go to Settings > Billing, and click 'Cancel Subscription'. You can also contact our support team for assistance.",
                    "category": "Billing",
                    "keywords": '["cancel", "subscription", "billing", "account"]',
                },
                {
                    "question": "How do I contact customer support?",
                    "answer": "You can contact customer support through this chat system, email us at support@company.com, or call us at 1-800-SUPPORT during business hours.",
                    "category": "Support",
                    "keywords": '["contact", "support", "help", "phone", "email"]',
                },
                {
                    "question": "What payment methods do you accept?",
                    "answer": "We accept all major credit cards (Visa, MasterCard, American Express), PayPal, and bank transfers. All payments are processed securely.",
                    "category": "Billing",
                    "keywords": '["payment", "credit card", "paypal", "billing", "methods"]',
                },
            ]

            for faq_data in sample_faqs:
                faq = FAQ(**faq_data)
                db.add(faq)

            await db.commit()
            logger.info(f"Populated {len(sample_faqs)} sample FAQs")

    except Exception as e:
        logger.error(f"Error populating FAQs: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
