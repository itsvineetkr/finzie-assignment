from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def process(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a message and return a response"""
        pass
    
    def log_interaction(self, message: str, response: Dict[str, Any]):
        """Log the interaction for debugging and monitoring"""
        self.logger.info(f"Agent: {self.name}")
        self.logger.info(f"Input: {message}")
        self.logger.info(f"Output: {response}")
