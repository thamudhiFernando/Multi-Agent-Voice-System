from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Enum defining the possible message roles in conversations"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class AgentType(str, Enum):
    """Enum defining the different agent types"""
    ORCHESTRATOR = "orchestrator"
    SALES = "sales"
    MARKETING = "marketing"
    TECHNICAL_SUPPORT = "technical_support"
    ORDER_LOGISTICS = "order_logistics"
    CUSTOMER_SERVICE = "customer_service"

class SentimentLabel(str, Enum):
    """Enum defining for sentiment classification labels"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


#Request Schemas
class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    channel_id: bool = Field(False, description="Whether input is from voice")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's the price of iPhone 15 Pro?",
                "session_id": "session_123456",
                "voice_input": False,
            }
        }

class VoiceRequest(BaseModel):
    """Request schema for voice endpoint"""
    audio_data: str = Field(None, description="Base64 encoded Audio data")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

    class Config:
        json_schema_extra = {
            "example": {
                "audio_data": "base64_encoded_audio_data",
                "session_id": "session_123456",
            }
        }

class FeedbackRequest(BaseModel):
    """Request schema for user feedback endpoint"""
    session_id: Optional[str] = Field(..., description="Session ID for conversation continuity")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(None, max_length=500, description="Optional feedback text")
    helpful: bool = Field(..., description="Whether feedback text is helpful")


#Response Schema
class AgentInfo(BaseModel):
    """Information about the agent that handled the request"""
    agent_type: AgentType
    confidence: float = Field(...,ge=0.0, le=1.0, description="Confidence score")

class SentimentInfo(BaseModel):
    """Sentiment analysis information"""
    label: SentimentLabel
    score: float = Field(..., ge=1.0, le=1.0, description="Sentiment score")

class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    response: str = Field(..., description="Agent response message")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    agent_info: AgentInfo
    sentiment: Optional[SentimentInfo] = None
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    timestamp: datetime
    suggestions: Optional[List[str]] = Field(None, description="Suggested follow-up questions")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "The iPhone 15 Pro is proces at $999.99...",
                "session_id": "session_123456",
                "agent_info": {
                    "agent_type": "sales",
                    "confidence": 0.95,
                },
                "sentiment": {
                    "label": "neutral",
                    "score": 0.05,
                },
                "response_time_ms": 1250,
                "timestamp": "2025-01-25T10:30:00",
                "suggestions": ["Compare with Samsung Galaxy S24","Check availability"]
            }
        }

class ConversationMessage(BaseModel):
    """Single Message schema in conversation history"""
    role: MessageRole
    content: str
    timestamp: datetime
    agent_type: Optional[AgentType] = None

class ConversationHistory(BaseModel):
    """Conversation History Response"""
    session_id: str
    messages: List[ConversationMessage]
    total_messages: int
