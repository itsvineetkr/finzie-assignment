import logging
import os
from datetime import datetime
from typing import Optional

def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('support_system.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def generate_ticket_number() -> str:
    """Generate a unique ticket number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TKT-{timestamp}"

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return str(uuid.uuid4())

def extract_keywords(text: str) -> list:
    """Extract keywords from text for FAQ matching"""
    import re
    # Simple keyword extraction - can be enhanced with NLP
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    import re
    # Simple phone validation - can be enhanced
    pattern = r'^\+?[\d\s\-\(\)]{10,}$'
    return re.match(pattern, phone) is not None
