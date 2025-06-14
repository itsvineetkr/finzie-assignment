from typing import Dict, Any
from agents.base_agent import BaseAgent
from schemas.models import IntentType


class RoutingAgent(BaseAgent):
    def __init__(self):
        super().__init__("Router")

        self.intent_to_agent = {
            IntentType.FAQ: "FAQAgent",
            IntentType.COMPLAINT: "TicketAgent",
            IntentType.ACCOUNT_INQUIRY: "AccountAgent",
            IntentType.GENERAL: "FAQAgent",
        }

    async def process(
        self, message: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Route the request to the appropriate support agent"""
        try:
            if not context or "intent" not in context:
                raise ValueError("Intent information required for routing")

            intent = context["intent"]

            target_agent = self.intent_to_agent.get(intent, "FAQAgent")

            result = {
                "target_agent": target_agent,
                "intent": intent,
                "routing_reason": f"Intent '{intent}' mapped to {target_agent}",
                "agent": self.name,
            }

            self.log_interaction(f"Intent: {intent}", result)
            return result

        except Exception as e:
            self.logger.error(f"Error in routing: {e}")
            return {
                "target_agent": "FAQAgent",
                "intent": IntentType.GENERAL,
                "routing_reason": f"Error in routing, defaulting to FAQAgent: {str(e)}",
                "agent": self.name,
                "error": str(e),
            }

    def get_available_agents(self) -> Dict[str, str]:
        """Return available agents and their descriptions"""
        return {
            "FAQAgent": "Handles general questions and FAQ responses",
            "TicketAgent": "Handles complaints and creates support tickets",
            "AccountAgent": "Handles account-related inquiries and issues",
        }
