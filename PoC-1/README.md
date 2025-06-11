# Cogniwide AI Voice Agent System - POC-1

A FastAPI-based voice agent system that integrates with Vapi to handle outbound calls and process voice interactions.

## Features

- Outbound call initiation
- Webhook handling for Vapi events
- Call data storage and analytics
- Conversation tracking
- Intent analysis and success evaluation

## Prerequisites

- Python 3.8+
- SQLite
- ngrok (for webhook URL)
- Vapi account and API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/itsvineetkr/finzie-assignment.git
cd finzie-assignment
cd PoC-1
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install fastapi uvicorn sqlite3 logging
```

## Project Structure

```
app/
├── main.py              # Main FastAPI application
├── webhook_handlers.py  # Webhook routes and handlers
├── database.py          # Database initialization and operations
├── call_logic.py        # Outbound call logic
├── config.py            # Configurations
└── schemas.py           # Pydantic models
```

## Configuration

1. Set up your environment variables (create a `.env` file):
```
VAPI_API_KEY=your_vapi_api_key_here
VAPI_ASSISTANT_ID=your_default_assistant_id
VAPI_PHONE_NUMBER_ID=your_phone_number_id
```

2. The system will automatically create an SQLite database (`voice_agent.db`) on first run.

## Database Schema

The system creates the following tables:
- `calls` - Call records and metadata
- `conversations` - Message-by-message conversation data
- `call_intents` - Intent analysis and success evaluation
- `outbound_requests` - Outbound call request tracking

## Running the Application

1. Start the FastAPI server:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. The API will be available at `http://localhost:8000`

## Setting up ngrok for Webhook URL

To receive webhooks from Vapi, you need to expose your local server to the internet using ngrok:

1. Install ngrok:
   - Download from https://ngrok.com/download
   - Extract and add to your PATH

2. Start ngrok tunnel:
```bash
ngrok http 8000
```

3. Copy the HTTPS URL from ngrok output (e.g., `https://abc123.ngrok.io`)

4. Configure Vapi webhook:
   - Go to your Vapi dashboard
   - Navigate to Settings > Webhooks
   - Set the webhook URL to: `https://your-ngrok-url.ngrok.io/webhook`
   - Save the configuration

## API Endpoints

### Core Endpoints

- `POST /make-call` - Initiate an outbound call
- `POST /webhook` - Receive Vapi events (for ngrok)
- `GET /calls` - List all calls with intent data
- `GET /calls/{call_id}` - Get detailed call conversation
- `GET /outbound-requests` - List all outbound call requests
- `GET /analytics` - Get call statistics and analytics
- `GET /` - API information and available endpoints

### Making an Outbound Call

```bash
curl -X POST "http://localhost:8000/make-call" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "assistant_id": "optional-assistant-id",
    "first_message": "Hello, this is a test call",
    "purpose": "Customer support"
  }'
```

### Response Format

```json
{
  "status": "success",
  "call_id": "call-uuid",
  "message": "Call initiated successfully to +1234567890"
}
```

## Webhook Event Handling

The system handles various Vapi events:
- `status-update` - Call status changes
- `end-of-call-report` - Complete call data and conversation
- All events are automatically saved to the database

## Analytics and Monitoring

Access analytics at `/analytics` to view:
- Total calls made
- Average call duration
- Total cost
- Intent distribution
- Success rate statistics

### Common Issues

1. **Webhook Not Receiving Events**: 
   - Verify ngrok is running and tunnel is active
   - Check that the webhook URL in Vapi dashboard is correct 
      (on Vapi Dashboard--> Assistants --> Your Assistant --> Messaging --> ServerURL)
   - Ensure the URL ends with `/webhook`

2. **Call Initiation Fails**: 
   - Verify Vapi API credentials are correct
   - Check that the phone number format is valid
   - Ensure sufficient credits in Vapi account
   - On free account it only supports calls to USA and doesn't support international calls.
