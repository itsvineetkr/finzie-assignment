from fastapi import HTTPException
import requests
import sqlite3
from datetime import datetime
import logging

from app.config import VAPI_API_KEY, VAPI_ASSISTANT_ID, VAPI_PHONE_NUMBER_ID


logger = logging.getLogger(__name__)


def extract_intent_from_conversation(messages, summary=None):
    """Extract intent from conversation messages"""
    user_messages = [msg["message"] for msg in messages if msg["role"] == "user"]
    bot_messages = [msg["message"] for msg in messages if msg["role"] == "bot"]

    # Simple intent classification logic
    intent = "unknown"
    confidence = 0.5
    extracted_data = {}

    conversation_text = " ".join(user_messages + bot_messages).lower()

    if "schedule" in conversation_text or "callback" in conversation_text:
        intent = "schedule_callback"
        confidence = 0.8
    elif "resolved" in conversation_text or "fixed" in conversation_text:
        intent = "issue_resolved"
        confidence = 0.9
    elif "problem" in conversation_text or "issue" in conversation_text:
        intent = "report_issue"
        confidence = 0.7
    elif "complaint" in conversation_text:
        intent = "complaint"
        confidence = 0.8

    extracted_data = {
        "user_responses": user_messages,
        "bot_responses": bot_messages,
        "conversation_length": len(messages),
    }

    return intent, confidence, extracted_data


def log_outbound_request(
    phone_number: str,
    assistant_id: str,
    purpose: str,
    status: str = "initiated",
    call_id: str = None,
    error_message: str = None,
):
    """Log outbound call request to database"""
    conn = sqlite3.connect("voice_agent.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO outbound_requests 
            (phone_number, assistant_id, purpose, status, call_id, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (phone_number, assistant_id, purpose, status, call_id, error_message),
        )

        conn.commit()
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"Error logging outbound request: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()


async def make_outbound_call(
    phone_number: str,
    assistant_id: str = None,
    first_message: str = None,
    purpose: str = "Customer outreach",
):
    """Make an outbound call using Vapi API"""

    # Use default assistant if not provided
    if not assistant_id:
        assistant_id = VAPI_ASSISTANT_ID

    # Validate required configuration
    if not VAPI_API_KEY:
        raise HTTPException(status_code=500, detail="Vapi API key not configured")

    if not assistant_id:
        raise HTTPException(status_code=500, detail="Vapi Assistant ID not configured")

    # Prepare API request
    url = "https://api.vapi.ai/call"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"assistantId": assistant_id, "customer": {"number": phone_number}}

    # Add phone number ID if available
    if VAPI_PHONE_NUMBER_ID:
        payload["phoneNumberId"] = VAPI_PHONE_NUMBER_ID

    # Add custom first message if provided
    if first_message:
        payload["assistantOverrides"] = {"firstMessage": first_message}

    try:
        logger.info(f"Making outbound call to {phone_number}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 201:
            call_data = response.json()
            call_id = call_data.get("id")

            # Log successful request
            log_outbound_request(
                phone_number, assistant_id, purpose, "success", call_id
            )

            # Store initial call record
            conn = sqlite3.connect("voice_agent.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO calls 
                (id, type, phone_number, status, purpose, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    call_id,
                    "outbound",
                    phone_number,
                    "initiated",
                    purpose,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()

            logger.info(f"✅ Successfully initiated call {call_id} to {phone_number}")
            return {"success": True, "call_id": call_id, "data": call_data}

        else:
            error_msg = f"Vapi API error: {response.status_code} - {response.text}"
            logger.error(error_msg)

            # Log failed request
            log_outbound_request(
                phone_number, assistant_id, purpose, "failed", error_message=error_msg
            )

            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code,
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg)

        # Log failed request
        log_outbound_request(
            phone_number, assistant_id, purpose, "failed", error_message=error_msg
        )

        return {"success": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)

        # Log failed request
        log_outbound_request(
            phone_number, assistant_id, purpose, "failed", error_message=error_msg
        )

        return {"success": False, "error": error_msg}
