import os
import openai
from typing import Dict, Any
from agents.base_agent import BaseAgent
from utils.prompts import INTENT_CLASSIFICATION_PROMPT
from schemas.models import IntentType
import re

class IntentClassifierAgent(BaseAgent):
    """Agent responsible for classifying user intent"""
    
    def __init__(self):
        super().__init__("IntentClassifier")
        self.openai_client = None
        self.use_openai = False
        
        # Try to initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
                self.use_openai = True
                self.logger.info("OpenAI client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.use_openai = False
        else:
            self.logger.info("OpenAI API key not configured, using keyword-based classification")
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Classify the intent of the user message"""
        try:
            if self.use_openai:
                intent, reasoning = await self._classify_with_openai(message)
            else:
                intent, reasoning = self._classify_with_keywords(message)
            
            result = {
                "intent": intent,
                "confidence": 0.8 if self.use_openai else 0.6,
                "reasoning": reasoning,
                "agent": self.name
            }
            
            self.log_interaction(message, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in intent classification: {e}")
            return {
                "intent": IntentType.GENERAL,
                "confidence": 0.5,
                "reasoning": "Failed to classify, defaulting to general",
                "agent": self.name,
                "error": str(e)
            }
    
    async def _classify_with_openai(self, message: str) -> tuple:
        """Classify intent using OpenAI API"""
        try:
            prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert intent classification system."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the response
            intent_match = re.search(r'INTENT:\s*(\w+)', content)
            reasoning_match = re.search(r'REASONING:\s*(.+)', content)
            
            if intent_match:
                intent_str = intent_match.group(1).upper()
                try:
                    intent = IntentType(intent_str.lower())
                except ValueError:
                    intent = IntentType.GENERAL
            else:
                intent = IntentType.GENERAL
            
            reasoning = reasoning_match.group(1) if reasoning_match else "OpenAI classification"
            
            return intent, reasoning
            
        except Exception as e:
            self.logger.error(f"OpenAI classification failed: {e}")
            return self._classify_with_keywords(message)
    
    def _classify_with_keywords(self, message: str) -> tuple:
        """Classify intent using keyword matching"""
        message_lower = message.lower()

        patterns = {
            IntentType.FAQ: [
                r'\b(how|what|when|where|why|can|could|would|should)\b',
                r'\b(help|guide|tutorial|instructions|explain)\b',
                r'\b(policy|procedure|process|steps)\b'
            ],
            IntentType.COMPLAINT: [
                r'\b(problem|issue|error|bug|broken|not working|failed|wrong)\b',
                r'\b(complain|complaint|unhappy|dissatisfied|angry|frustrated)\b',
                r'\b(refund|cancel|dispute|report)\b'
            ],
            IntentType.ACCOUNT_INQUIRY: [
                r'\b(account|profile|billing|payment|subscription|plan)\b',
                r'\b(login|password|username|access|verify|update)\b',
                r'\b(balance|charge|invoice|transaction)\b'
            ]
        }
        
        scores = {}
        for intent, intent_patterns in patterns.items():
            score = 0
            matched_patterns = []
            for pattern in intent_patterns:
                matches = re.findall(pattern, message_lower)
                if matches:
                    score += len(matches)
                    matched_patterns.append(pattern)
            scores[intent] = (score, matched_patterns)
        
        best_intent = IntentType.GENERAL
        best_score = 0
        reasoning = "No specific keywords matched"
        
        for intent, (score, patterns) in scores.items():
            if score > best_score:
                best_intent = intent
                best_score = score
                reasoning = f"Matched patterns: {patterns[:2]}"
        
        if best_score == 0:
            reasoning = "No specific intent keywords found, classified as general inquiry"
        
        return best_intent, reasoning
