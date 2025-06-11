from fastapi import APIRouter, Request, HTTPException
import logging
from app.database import save_call_data


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook")
async def receive_vapi_event(request: Request):
    """Webhook endpoint to receive Vapi events"""
    try:
        data = await request.json()
        print(data)
        event_type = data.get("message", {}).get("type", "unknown")

        logger.info(f"Incoming event from Vapi: {event_type}")

        print("save to karne ja rhe hai bhai")
        # Save all call data to database
        save_call_data(data.get("message", {}))

        print("save function to run ho gya bhai")

        # Handle different event types
        if event_type == "status-update":
            logger.info("Call status update received")
        elif event_type == "end-of-call-report":
            logger.info("End of call report received - processing conversation")

        return {"status": "received", "event_type": event_type}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
