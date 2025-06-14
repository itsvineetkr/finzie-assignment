from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from agents.base_agent import BaseAgent
from models.database import FAQ, Ticket, ChatMessage
from utils.prompts import FAQ_AGENT_PROMPT, COMPLAINT_AGENT_PROMPT, ACCOUNT_AGENT_PROMPT
from utils.helpers import generate_ticket_number, extract_keywords
from schemas.models import IntentType, TicketStatus
import json

class FAQAgent(BaseAgent):
    def __init__(self, db_session: AsyncSession):
        super().__init__("FAQAgent")
        self.db_session = db_session
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process FAQ requests"""
        try:
            
            relevant_faqs = await self._search_faqs(message)
            
            # Generate response using FAQ data
            response = await self._generate_faq_response(message, relevant_faqs)
            
            result = {
                "response": response,
                "agent": self.name,
                "faqs_found": len(relevant_faqs),
                "relevant_faqs": [{"question": faq.question, "answer": faq.answer} for faq in relevant_faqs[:3]]
            }
            
            self.log_interaction(message, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in FAQ processing: {e}")
            return {
                "response": "I apologize, but I'm having trouble accessing our FAQ database right now. Please try again later or contact our support team directly.",
                "agent": self.name,
                "error": str(e)
            }
    
    async def _search_faqs(self, message: str) -> List[FAQ]:
        """Search for relevant FAQs based on the message"""
        try:
            # Extract keywords from the message
            keywords = extract_keywords(message)
            
            # Query FAQs
            stmt = select(FAQ).where(FAQ.is_active == True)
            result = await self.db_session.execute(stmt)
            all_faqs = result.scalars().all()
            
            # Score FAQs based on keyword matching
            scored_faqs = []
            for faq in all_faqs:
                score = self._calculate_faq_score(message, keywords, faq)
                if score > 0:
                    scored_faqs.append((faq, score))
            
            # Sort by score and return top matches
            scored_faqs.sort(key=lambda x: x[1], reverse=True)
            return [faq for faq, score in scored_faqs[:5]]
            
        except Exception as e:
            self.logger.error(f"Error searching FAQs: {e}")
            return []
    
    def _calculate_faq_score(self, message: str, keywords: List[str], faq: FAQ) -> float:
        """Calculate relevance score for an FAQ"""
        score = 0.0
        message_lower = message.lower()
        faq_text = f"{faq.question} {faq.answer}".lower()
        
        # Check for direct keyword matches
        for keyword in keywords:
            if keyword in faq_text:
                score += 1.0
        
        # Check for FAQ-specific keywords if available
        if faq.keywords:
            try:
                faq_keywords = json.loads(faq.keywords)
                for faq_keyword in faq_keywords:
                    if faq_keyword.lower() in message_lower:
                        score += 1.5
            except:
                pass
        
        return score
    
    async def _generate_faq_response(self, message: str, faqs: List[FAQ]) -> str:
        """Generate a response based on found FAQs"""
        if not faqs:
            return """I don't have a specific FAQ that matches your question, but I'd be happy to help! 
            
Here are a few things you can try:
• Check our help center for more detailed guides
• Contact our support team for personalized assistance
• Try rephrasing your question with different keywords

Is there anything specific I can help you with?"""
        
        # Use the best matching FAQ
        best_faq = faqs[0]
        
        response = f"""Based on your question, here's what I found:

**Q: {best_faq.question}**
**A: {best_faq.answer}**
"""
        
        # Add additional FAQs if they're relevant
        if len(faqs) > 1:
            response += "\n\n**You might also find these helpful:**\n"
            for faq in faqs[1:3]:  # Show up to 2 more
                response += f"• {faq.question}\n"
        
        response += "\n\nIf this doesn't answer your question, please let me know and I'll be happy to help further!"
        
        return response

class TicketAgent(BaseAgent):
    """Agent for handling complaints and creating tickets"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__("TicketAgent")
        self.db_session = db_session
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process complaint and create ticket"""
        try:
            # Create a ticket for the complaint
            ticket = await self._create_ticket(message, context)
            
            # Generate response
            response = await self._generate_complaint_response(message, ticket.ticket_number)
            
            result = {
                "response": response,
                "agent": self.name,
                "ticket_number": ticket.ticket_number,
                "ticket_id": ticket.id,
                "requires_notification": True
            }
            
            self.log_interaction(message, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in ticket processing: {e}")
            return {
                "response": "I apologize for the inconvenience. I'm currently unable to create a support ticket, but your concern is important to us. Please try again later or contact our support team directly.",
                "agent": self.name,
                "error": str(e)
            }
    
    async def _create_ticket(self, message: str, context: Dict[str, Any]) -> Ticket:
        """Create a new support ticket"""
        ticket_number = generate_ticket_number()
        
        # Extract title from message (first 100 chars)
        title = message[:100] + "..." if len(message) > 100 else message
        
        ticket = Ticket(
            ticket_number=ticket_number,
            title=title,
            description=message,
            status=TicketStatus.OPEN,
            priority="medium",
            customer_email=context.get("customer_email") if context else None,
            customer_phone=context.get("customer_phone") if context else None,
            session_id=context.get("session_id") if context else None
        )
        
        self.db_session.add(ticket)
        await self.db_session.commit()
        await self.db_session.refresh(ticket)
        
        return ticket
    
    async def _generate_complaint_response(self, message: str, ticket_number: str) -> str:
        """Generate response for complaint"""
        return f"""I understand your concern and I'm sorry you're experiencing this issue. I want to make sure we address this properly.

I've created a support ticket for you:
**Ticket Number: {ticket_number}**

Here's what happens next:
• Your ticket has been assigned to our support team
• You'll receive a confirmation email shortly
• A support specialist will review your case within 24 hours
• We'll keep you updated on the progress

Your issue is important to us, and we're committed to resolving it as quickly as possible. Is there any additional information you'd like to add to your ticket?"""

class AccountAgent(BaseAgent):
    """Agent for handling account-related inquiries"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__("AccountAgent")
        self.db_session = db_session
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process account-related inquiries"""
        try:
            # Generate response for account inquiry
            response = await self._generate_account_response(message, context)
            
            result = {
                "response": response,
                "agent": self.name,
                "requires_verification": True
            }
            
            self.log_interaction(message, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in account processing: {e}")
            return {
                "response": "I apologize, but I'm currently unable to access account information. Please contact our support team directly for account-related assistance.",
                "agent": self.name,
                "error": str(e)
            }
    
    async def _generate_account_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate response for account inquiry"""
        return """I'd be happy to help you with your account inquiry. 

For security reasons, I cannot access specific account information in this chat. However, I can help you with:

**Common Account Tasks:**
• Password reset instructions
• Account verification steps
• Billing and payment information
• Profile update procedures

**For Specific Account Issues:**
To get detailed help with your account, please:
1. Visit our secure account portal
2. Contact our account specialists directly
3. Provide proper verification (email, phone, or security questions)

**Immediate Help:**
If this is urgent, I can create a priority ticket for our account team to contact you directly. Would you like me to do that?

What specific account issue can I help guide you through?"""
