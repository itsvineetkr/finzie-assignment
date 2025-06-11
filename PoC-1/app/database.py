import json
import sqlite3
import logging

from app.call_logic import extract_intent_from_conversation


logger = logging.getLogger(__name__)


def init_db():
    conn = sqlite3.connect("voice_agent.db")
    cursor = conn.cursor()

    # Create calls table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS calls (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            phone_number TEXT,
            status TEXT,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            duration_seconds REAL,
            cost REAL,
            ended_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create conversations table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT,
            role TEXT,
            message TEXT,
            timestamp BIGINT,
            seconds_from_start REAL,
            duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (call_id) REFERENCES calls (id)
        )
    """
    )

    # Create intents table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS call_intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT,
            intent TEXT,
            confidence REAL,
            extracted_data TEXT,
            summary TEXT,
            success_evaluation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (call_id) REFERENCES calls (id)
        )
    """
    )

    # For outbound calls
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS outbound_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            assistant_id TEXT,
            purpose TEXT,
            status TEXT DEFAULT 'initiated',
            call_id TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()


def save_call_data(call_data):
    """Save call data to database"""
    conn = sqlite3.connect("voice_agent.db")
    cursor = conn.cursor()

    try:
        call_info = call_data.get("call", {})
        call_id = call_info.get("id")

        print(call_info, call_id, sep="\n")

        if not call_id:
            logger.error("No call ID found in call data")
            return

        # Insert or update call record
        cursor.execute(
            """
            INSERT OR REPLACE INTO calls 
            (id, type, status, started_at, ended_at, duration_seconds, cost, ended_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                call_id,
                call_info.get("type", "unknown"),
                call_data.get("message", {}).get("status", "unknown"),
                call_data.get("startedAt"),
                call_data.get("endedAt"),
                call_data.get("durationSeconds"),
                call_data.get("cost"),
                call_data.get("endedReason"),
            ),
        )

        # Save conversation messages if available
        messages = call_data.get("messages", [])
        for msg in messages:
            if msg["role"] != "system":  # Skip system messages
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO conversations 
                    (call_id, role, message, timestamp, seconds_from_start, duration)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        call_id,
                        msg["role"],
                        msg["message"],
                        msg.get("time"),
                        msg.get("secondsFromStart"),
                        msg.get("duration"),
                    ),
                )

        # Extract and save intent if this is an end-of-call report
        if call_data.get("message", {}).get("type") == "end-of-call-report":
            intent, confidence, extracted_data = extract_intent_from_conversation(
                messages
            )
            summary = call_data.get("summary", "")
            success_eval = call_data.get("analysis", {}).get("successEvaluation", "")

            cursor.execute(
                """
                INSERT OR REPLACE INTO call_intents 
                (call_id, intent, confidence, extracted_data, summary, success_evaluation)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    call_id,
                    intent,
                    confidence,
                    json.dumps(extracted_data),
                    summary,
                    success_eval,
                ),
            )

        conn.commit()
        logger.info(f"Successfully saved call data for call ID: {call_id}")

    except Exception as e:
        logger.error(f"Error saving call data: {str(e)}")
        print("Error saving call data:", str(e))
        conn.rollback()
    finally:
        conn.close()


{
    "message": {
        "timestamp": 1749546420647,
        "type": "status-update",
        "status": "in-progress",
        "artifact": {
            "messages": [
                {
                    "role": "system",
                    "message": "You are a helpful customer support agent for Cogniwide.\nGreet the user, ask if their internet issue is resolved.\nIf yes, say thanks and end the call.\nIf no, ask if they want to schedule a callback.",
                    "time": 1749546415876,
                    "secondsFromStart": 0,
                }
            ],
            "messagesOpenAIFormatted": [
                {
                    "role": "system",
                    "content": "You are a helpful customer support agent for Cogniwide.\nGreet the user, ask if their internet issue is resolved.\nIf yes, say thanks and end the call.\nIf no, ask if they want to schedule a callback.",
                }
            ],
        },
        "call": {
            "id": "73daba4d-2bcc-4cca-8e49-3d7903467ade",
            "orgId": "aeccb59a-73ea-4033-baae-51833f9ed571",
            "createdAt": "2025-06-10T09:06:55.710Z",
            "updatedAt": "2025-06-10T09:06:55.710Z",
            "type": "webCall",
            "monitor": {
                "listenUrl": "wss://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade/listen",
                "controlUrl": "https://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade/control",
            },
            "transport": {
                "provider": "daily",
                "assistantVideoEnabled": False,
                "callUrl": "https://vapi.daily.co/yJPTsCsAtxVnVkqIgWyZ",
            },
            "webCallUrl": "https://vapi.daily.co/yJPTsCsAtxVnVkqIgWyZ",
            "status": "queued",
            "assistantId": "054ea7e1-a5fc-4b9c-8c7c-9c6e80d21921",
            "assistantOverrides": {"clientMessages": ["transfer-update", "transcript"]},
        },
        "assistant": {
            "id": "054ea7e1-a5fc-4b9c-8c7c-9c6e80d21921",
            "orgId": "aeccb59a-73ea-4033-baae-51833f9ed571",
            "name": "Finzie",
            "voice": {"voiceId": "Elliot", "provider": "vapi"},
            "createdAt": "2025-06-10T07:49:12.531Z",
            "updatedAt": "2025-06-10T09:05:22.146Z",
            "model": {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful customer support agent for Cogniwide.\nGreet the user, ask if their internet issue is resolved.\nIf yes, say thanks and end the call.\nIf no, ask if they want to schedule a callback.",
                    }
                ],
                "provider": "openai",
                "temperature": 0.7,
            },
            "firstMessage": "Hello.",
            "voicemailMessage": "Please call back when you're available.",
            "endCallMessage": "Goodbye.",
            "transcriber": {
                "model": "nova-2",
                "language": "en",
                "provider": "deepgram",
            },
            "clientMessages": ["transfer-update", "transcript"],
            "server": {
                "url": "https://40d8-183-82-160-130.ngrok-free.app/webhook",
                "timeoutSeconds": 20,
            },
        },
    }
}


{
    "message": {
        "timestamp": 1749546450909,
        "type": "end-of-call-report",
        "analysis": {
            "summary": "The AI called to follow up on a user's internet issue. The user confirmed that the issue had been resolved, and the AI ended the call after receiving this confirmation.",
            "successEvaluation": "true",
        },
        "artifact": {
            "messages": [
                {
                    "role": "system",
                    "message": "You are a helpful customer support agent for Cogniwide.\nGreet the user, ask if their internet issue is resolved.\nIf yes, say thanks and end the call.\nIf no, ask if they want to schedule a callback.",
                    "time": 1749546415876,
                    "secondsFromStart": 0,
                },
                {
                    "role": "bot",
                    "message": "Hello?",
                    "time": 1749546417519,
                    "endTime": 1749546418019,
                    "secondsFromStart": 1.28,
                    "duration": 500,
                    "source": "",
                },
                {
                    "role": "user",
                    "message": "Okay.",
                    "time": 1749546419759,
                    "endTime": 1749546420259,
                    "secondsFromStart": 3.52,
                    "duration": 500,
                },
                {
                    "role": "bot",
                    "message": "Hi there. I hope you're doing well. I wanted to check-in see if your Internet issue has been resolved.",
                    "time": 1749546422419,
                    "endTime": 1749546429009,
                    "secondsFromStart": 6.18,
                    "duration": 6280,
                    "source": "",
                },
                {
                    "role": "user",
                    "message": "Yes. It has been.",
                    "time": 1749546430259,
                    "endTime": 1749546431559,
                    "secondsFromStart": 14.02,
                    "duration": 1300,
                },
                {
                    "role": "bot",
                    "message": "That's great to hear. You for letting me know. Um, if you need any further assistance in the future, feel free to reach out. Have a wonderful day.",
                    "time": 1749546432989,
                    "endTime": 1749546441049,
                    "secondsFromStart": 16.75,
                    "duration": 7030,
                    "source": "",
                },
            ],
            "messagesOpenAIFormatted": [
                {
                    "role": "system",
                    "content": "You are a helpful customer support agent for Cogniwide.\nGreet the user, ask if their internet issue is resolved.\nIf yes, say thanks and end the call.\nIf no, ask if they want to schedule a callback.",
                },
                {"role": "assistant", "content": "Hello?"},
                {"role": "user", "content": "Okay."},
                {
                    "role": "assistant",
                    "content": "Hi there. I hope you're doing well. I wanted to check-in see if your Internet issue has been resolved.",
                },
                {"role": "user", "content": "Yes. It has been."},
                {
                    "role": "assistant",
                    "content": "That's great to hear. You for letting me know. Um, if you need any further assistance in the future, feel free to reach out. Have a wonderful day.",
                },
            ],
            "transcript": "AI: Hello?\nUser: Okay.\nAI: Hi there. I hope you're doing well. I wanted to check-in see if your Internet issue has been resolved.\nUser: Yes. It has been.\nAI: That's great to hear. You for letting me know. Um, if you need any further assistance in the future, feel free to reach out. Have a wonderful day.\n",
            "recordingUrl": "https://storage.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade-1749546448431-3ef3457e-6fe6-4410-b76d-7b135cd4901e-mono.wav",
            "stereoRecordingUrl": "https://storage.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade-1749546448431-2df6e5bd-59d4-4ef3-81d5-7024bef0ce08-stereo.wav",
            "recording": {
                "stereoUrl": "https://storage.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade-1749546448431-2df6e5bd-59d4-4ef3-81d5-7024bef0ce08-stereo.wav",
                "mono": {
                    "combinedUrl": "https://storage.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade-1749546448431-3ef3457e-6fe6-4410-b76d-7b135cd4901e-mono.wav",
                    "assistantUrl": "https://storage.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade-1749546448431-40c52d21-edb4-45e3-bacd-8c607f779a93-mono.wav",
                    "customerUrl": "https://storage.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade-1749546448431-9ab3c0a5-d478-4277-93cc-189a4b7c9e62-mono.wav",
                },
            },
            "nodes": [],
            "variables": {},
        },
        "startedAt": "2025-06-10T09:07:00.649Z",
        "endedAt": "2025-06-10T09:07:25.925Z",
        "endedReason": "customer-ended-call",
        "cost": 0.0394,
        "costBreakdown": {
            "stt": 0.0056,
            "llm": 0.0001,
            "tts": 0.0126,
            "vapi": 0.0211,
            "total": 0.0394,
            "llmPromptTokens": 257,
            "llmCompletionTokens": 57,
            "ttsCharacters": 251,
            "voicemailDetectionCost": 0,
            "knowledgeBaseCost": 0,
            "analysisCostBreakdown": {
                "summary": 0,
                "summaryPromptTokens": 147,
                "summaryCompletionTokens": 35,
                "structuredData": 0,
                "structuredDataPromptTokens": 0,
                "structuredDataCompletionTokens": 0,
                "successEvaluation": 0,
                "successEvaluationPromptTokens": 251,
                "successEvaluationCompletionTokens": 1,
            },
        },
        "costs": [
            {
                "type": "transcriber",
                "transcriber": {"provider": "deepgram", "model": "nova-2"},
                "minutes": 0.5009166666666667,
                "cost": 0.00562928,
            },
            {
                "type": "model",
                "model": {"provider": "openai", "model": "gpt-4o-mini"},
                "promptTokens": 257,
                "completionTokens": 57,
                "cost": 7.275e-05,
            },
            {
                "type": "voice",
                "voice": {
                    "provider": "vapi",
                    "voiceId": "dN8hviqdNrAsEcL57yFj",
                    "model": "eleven_turbo_v2_5",
                },
                "characters": 251,
                "cost": 0.01255,
            },
            {"type": "vapi", "subType": "normal", "minutes": 0.4213, "cost": 0.021065},
            {
                "type": "analysis",
                "analysisType": "summary",
                "model": {
                    "provider": "google",
                    "model": "gemini-2.5-flash-preview-04-17",
                },
                "promptTokens": 147,
                "completionTokens": 35,
                "cost": 4.305e-05,
            },
            {
                "type": "analysis",
                "analysisType": "successEvaluation",
                "model": {
                    "provider": "google",
                    "model": "gemini-2.5-flash-preview-04-17",
                },
                "promptTokens": 251,
                "completionTokens": 1,
                "cost": 3.825e-05,
            },
            {
                "type": "knowledge-base",
                "model": {"provider": "google", "model": "gemini-1.5-flash"},
                "promptTokens": 0,
                "completionTokens": 0,
                "cost": 0,
            },
        ],
        "durationMs": 25276,
        "durationSeconds": 25.276,
        "durationMinutes": 0.4213,
        "summary": "The AI called to follow up on a user's internet issue. The user confirmed that the issue had been resolved, and the AI ended the call after receiving this confirmation.",
        "transcript": "AI: Hello?\nUser: Okay.\nAI: Hi there. I hope you're doing well. I wanted to check-in see if your Internet issue has been resolved.\nUser: Yes. It has been.\nAI: That's great to hear. You for letting me know. Um, if you need any further assistance in the future, feel free to reach out. Have a wonderful day.\n",
        "messages": [
            {
                "role": "system",
                "message": "You are a helpful customer support agent for Cogniwide.\nGreet the user, ask if their internet issue is resolved.\nIf yes, say thanks and end the call.\nIf no, ask if they want to schedule a callback.",
                "time": 1749546415876,
                "secondsFromStart": 0,
            },
            {
                "role": "bot",
                "message": "Hello?",
                "time": 1749546417519,
                "endTime": 1749546418019,
                "secondsFromStart": 1.28,
                "duration": 500,
                "source": "",
            },
            {
                "role": "user",
                "message": "Okay.",
                "time": 1749546419759,
                "endTime": 1749546420259,
                "secondsFromStart": 3.52,
                "duration": 500,
            },
            {
                "role": "bot",
                "message": "Hi there. I hope you're doing well. I wanted to check-in see if your Internet issue has been resolved.",
                "time": 1749546422419,
                "endTime": 1749546429009,
                "secondsFromStart": 6.18,
                "duration": 6280,
                "source": "",
            },
            {
                "role": "user",
                "message": "Yes. It has been.",
                "time": 1749546430259,
                "endTime": 1749546431559,
                "secondsFromStart": 14.02,
                "duration": 1300,
            },
            {
                "role": "bot",
                "message": "That's great to hear. You for letting me know. Um, if you need any further assistance in the future, feel free to reach out. Have a wonderful day.",
                "time": 1749546432989,
                "endTime": 1749546441049,
                "secondsFromStart": 16.75,
                "duration": 7030,
                "source": "",
            },
        ],
        "recordingUrl": "https://storage.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade-1749546448431-3ef3457e-6fe6-4410-b76d-7b135cd4901e-mono.wav",
        "stereoRecordingUrl": "https://storage.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade-1749546448431-2df6e5bd-59d4-4ef3-81d5-7024bef0ce08-stereo.wav",
        "call": {
            "id": "73daba4d-2bcc-4cca-8e49-3d7903467ade",
            "orgId": "aeccb59a-73ea-4033-baae-51833f9ed571",
            "createdAt": "2025-06-10T09:06:55.710Z",
            "updatedAt": "2025-06-10T09:06:55.710Z",
            "type": "webCall",
            "monitor": {
                "listenUrl": "wss://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade/listen",
                "controlUrl": "https://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/73daba4d-2bcc-4cca-8e49-3d7903467ade/control",
            },
            "transport": {
                "provider": "daily",
                "assistantVideoEnabled": False,
                "callUrl": "https://vapi.daily.co/yJPTsCsAtxVnVkqIgWyZ",
            },
            "webCallUrl": "https://vapi.daily.co/yJPTsCsAtxVnVkqIgWyZ",
            "status": "queued",
            "assistantId": "054ea7e1-a5fc-4b9c-8c7c-9c6e80d21921",
            "assistantOverrides": {"clientMessages": ["transfer-update", "transcript"]},
        },
        "assistant": {
            "id": "054ea7e1-a5fc-4b9c-8c7c-9c6e80d21921",
            "orgId": "aeccb59a-73ea-4033-baae-51833f9ed571",
            "name": "Finzie",
            "voice": {"voiceId": "Elliot", "provider": "vapi"},
            "createdAt": "2025-06-10T07:49:12.531Z",
            "updatedAt": "2025-06-10T09:05:22.146Z",
            "model": {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful customer support agent for Cogniwide.\nGreet the user, ask if their internet issue is resolved.\nIf yes, say thanks and end the call.\nIf no, ask if they want to schedule a callback.",
                    }
                ],
                "provider": "openai",
                "temperature": 0.7,
            },
            "firstMessage": "Hello.",
            "voicemailMessage": "Please call back when you're available.",
            "endCallMessage": "Goodbye.",
            "transcriber": {
                "model": "nova-2",
                "language": "en",
                "provider": "deepgram",
            },
            "clientMessages": ["transfer-update", "transcript"],
            "server": {
                "url": "https://40d8-183-82-160-130.ngrok-free.app/webhook",
                "timeoutSeconds": 20,
            },
        },
    }
}
