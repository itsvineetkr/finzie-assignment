# AI Multi-Agent Chat Support System (PoC-2)

## Features

- **Multi-Agent Architecture**: Specialized agents for different types of customer inquiries
- **Intent Classification**: AI-powered intent recognition using OpenAI or keyword-based fallback
- **Smart Routing**: Automatic routing to appropriate support agents
- **Support Agents**: 
  - FAQ Agent for general questions
  - Ticket Agent for complaints and issues
  - Account Agent for account-related inquiries
- **Notification System**: Email and SMS/WhatsApp notifications via SendGrid and Twilio
- **Database Integration**: SQLite/PostgreSQL for conversation logs and ticketing
- **Modern Web Interface**: Responsive chat interface with real-time updates
- **Error Handling**: Comprehensive error handling and fallback mechanisms

## System Architecture

```
User Query → Intent Classifier → Router → Support Agent → Notification Agent
                     ↓                         ↓              ↓
                 Database         ←    Response Generation   ←   External APIs
```

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .example_env .env
   # Edit .env with your API keys
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```

4. **Access the Interface**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Configuration

### Required Environment Variables

```env
# OpenAI (Optional - falls back to keyword classification)
OPENAI_API_KEY=your_openai_api_key_here

# Twilio (Optional - for SMS/WhatsApp notifications)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# SendGrid (Optional - for email notifications)
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=your_verified_sendgrid_email

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### Main Chat Endpoint
```http
POST /api/chat
Content-Type: application/json

{
  "message": "I need help with my account",
  "session_id": "optional_session_id",
  "customer_email": "user@example.com",
  "customer_phone": "+1234567890"
}
```

### Intent Classification Test
```http
POST /api/classify-intent
Content-Type: application/json

{
  "message": "I want to cancel my subscription"
}
```

## Agent System

### Intent Classifier Agent
- Uses OpenAI GPT-3.5 or keyword-based classification
- Classifies intents: FAQ, COMPLAINT, ACCOUNT_INQUIRY, GENERAL
- Provides confidence scores and reasoning

### Routing Agent
- Routes requests to appropriate support agents
- Maintains agent capability mapping
- Handles fallback routing

### Support Agents

#### FAQ Agent
- Searches knowledge base for relevant FAQs
- Provides helpful responses for general questions
- Auto-populates with sample FAQs on startup

#### Ticket Agent
- Creates support tickets for complaints
- Generates unique ticket numbers
- Handles escalation workflows

#### Account Agent
- Handles account-related inquiries
- Provides secure account guidance
- Recommends verification procedures

### Notification Agent
- Sends email notifications via SendGrid
- Sends SMS/WhatsApp via Twilio
- Tracks notification status and delivery

## Database Schema

### Tables
- `chat_messages` - Conversation history
- `tickets` - Support ticket tracking
- `faqs` - Knowledge base
- `notifications` - Notification logs

## Development

### Project Structure
```
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
├── agents/                 # Agent implementations
│   ├── base_agent.py
│   ├── intent_classifier.py
│   ├── routing_agent.py
│   ├── support_agents.py
│   └── notify_agent.py
├── database/               # Database connection
├── models/                 # SQLAlchemy models
├── schemas/                # Pydantic schemas
├── utils/                  # Utility functions
├── static/                 # Frontend assets
└── templates/              # HTML templates
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```
