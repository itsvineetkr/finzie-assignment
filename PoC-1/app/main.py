import logging
import sqlite3

from fastapi import FastAPI, HTTPException

from app.webhook_handlers import router as webhook_router
from app.database import init_db
from app.call_logic import make_outbound_call
from app.schemas import CallResponse, MakeCallRequest


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(webhook_router)

try:
    init_db()
except Exception as e:
    print("Couldn't create DB, error: ", e)


@app.post("/make-call", response_model=CallResponse)
async def initiate_outbound_call(request: MakeCallRequest):
    """
    Initiate an outbound call to a customer

    - **phone_number**: Customer's phone number (required)
    - **assistant_id**: Vapi assistant ID (optional, uses default if not provided)
    - **first_message**: Custom opening message (optional)
    - **purpose**: Purpose of the call for logging (optional)
    """
    try:
        # Validate phone number format
        if not request.phone_number or len(request.phone_number) < 10:
            raise HTTPException(
                status_code=400, detail="Valid phone number is required"
            )

        # Make the outbound call
        result = await make_outbound_call(
            phone_number=request.phone_number,
            assistant_id=request.assistant_id,
            first_message=request.first_message,
            purpose=request.purpose,
        )

        if result["success"]:
            return CallResponse(
                status="success",
                call_id=result["call_id"],
                message=f"Call initiated successfully to {request.phone_number}",
            )
        else:
            raise HTTPException(
                status_code=500, detail=f"Failed to initiate call: {result['error']}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in make_call endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/outbound-requests")
async def get_outbound_requests():
    """Get all outbound call requests and their status"""
    conn = sqlite3.connect("voice_agent.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT or.*, c.status as call_status, c.duration_seconds, c.cost
            FROM outbound_requests or
            LEFT JOIN calls c ON or.call_id = c.id
            ORDER BY or.created_at DESC
        """
        )

        requests_data = [dict(row) for row in cursor.fetchall()]
        return {"outbound_requests": requests_data}

    except Exception as e:
        logger.error(f"Error fetching outbound requests: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()


@app.get("/calls")
async def get_calls():
    """Get all calls from database"""
    conn = sqlite3.connect("voice_agent.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT c.*, ci.intent, ci.confidence, ci.summary, ci.success_evaluation
            FROM calls c
            LEFT JOIN call_intents ci ON c.id = ci.call_id
            ORDER BY c.created_at DESC
        """
        )

        calls = [dict(row) for row in cursor.fetchall()]
        return {"calls": calls}

    except Exception as e:
        logger.error(f"Error fetching calls: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()


@app.get("/calls/{call_id}")
async def get_call_details(call_id: str):
    """Get detailed conversation for a specific call"""
    conn = sqlite3.connect("voice_agent.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get call info
        cursor.execute("SELECT * FROM calls WHERE id = ?", (call_id,))
        call = cursor.fetchone()

        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        # Get conversation messages
        cursor.execute(
            """
            SELECT * FROM conversations 
            WHERE call_id = ? 
            ORDER BY seconds_from_start ASC
        """,
            (call_id,),
        )

        messages = [dict(row) for row in cursor.fetchall()]

        # Get intent data
        cursor.execute("SELECT * FROM call_intents WHERE call_id = ?", (call_id,))
        intent_data = cursor.fetchone()

        return {
            "call": dict(call),
            "messages": messages,
            "intent": dict(intent_data) if intent_data else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call details: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()


@app.get("/analytics")
async def get_analytics():
    """Get call analytics and statistics"""
    conn = sqlite3.connect("voice_agent.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Basic statistics
        cursor.execute("SELECT COUNT(*) as total_calls FROM calls")
        total_calls = cursor.fetchone()["total_calls"]

        cursor.execute(
            "SELECT AVG(duration_seconds) as avg_duration FROM calls WHERE duration_seconds IS NOT NULL"
        )
        avg_duration = cursor.fetchone()["avg_duration"] or 0

        cursor.execute(
            "SELECT SUM(cost) as total_cost FROM calls WHERE cost IS NOT NULL"
        )
        total_cost = cursor.fetchone()["total_cost"] or 0

        # Intent distribution
        cursor.execute(
            """
            SELECT intent, COUNT(*) as count 
            FROM call_intents 
            GROUP BY intent 
            ORDER BY count DESC
        """
        )
        intent_distribution = [dict(row) for row in cursor.fetchall()]

        # Success rate
        cursor.execute(
            """
            SELECT success_evaluation, COUNT(*) as count 
            FROM call_intents 
            WHERE success_evaluation IS NOT NULL
            GROUP BY success_evaluation
        """
        )
        success_stats = [dict(row) for row in cursor.fetchall()]

        return {
            "total_calls": total_calls,
            "average_duration_seconds": round(avg_duration, 2),
            "total_cost": round(total_cost, 4),
            "intent_distribution": intent_distribution,
            "success_statistics": success_stats,
        }

    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Cogniwide AI Voice Agent System - POC-1",
        "endpoints": {
            "webhook": "/webhook (POST) - Receive Vapi events",
            "calls": "/calls (GET) - List all calls",
            "call_details": "/calls/{call_id} (GET) - Get call conversation",
            "analytics": "/analytics (GET) - Get call statistics",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)