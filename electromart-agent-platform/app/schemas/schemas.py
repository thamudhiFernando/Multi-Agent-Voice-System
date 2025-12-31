from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, EmailStr


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


#Product Schemas
class ProductSpecs(BaseModel):
    """Product specifications schema (dynamic fields)"""
    class Config:
        #Allow additional fields
        extra = "allow"

class Product(BaseModel):
    """Product Information schema"""
    id: str
    name: str
    category: str
    brand: str
    price: float
    stock_status: str
    stock_quantity: int
    specs: Dict[str, Any]
    description: str


#Order Schemas
class OrderItem(BaseModel):
    """Single Item schema in an order"""
    product_id: str
    product_name: str
    quantity: int
    price: float

class Order(BaseModel):
    """Order details schema"""
    order_id: str
    customer_email: str
    customer_name: str
    order_date: str
    status: str
    items: List[OrderItem]
    total_amount: float
    shipping_address: str
    tracking_number: Optional[str] = None
    currier: Optional[str] = None
    estimated_delivery: Optional[str] = None
    shipping_status: str


#Promotion Schemas
class Promotion(BaseModel):
    """Promotion details schema"""
    id: str
    name: str
    description: str
    discount_type: str
    discount_amount: float
    applicable_category: List[str]
    start_date: str
    end_date: str
    status: str
    code: str
    requirements: Optional[str] = None

#Analytics Schemas
class AgentPerformance(BaseModel):
    """Agent performance metrics schema"""
    agent_type: AgentType
    total_queries: int
    success_rate: float
    avg_response_time_ms: float
    avg_confidence: float
    total_tokens_used: int

class SystemAnalytics(BaseModel):
    """Overall System Analytics schema"""
    total_conversation: int
    total_messages: int
    avg_sentiment_score: float
    agent_performance: List[AgentPerformance]
    timestamp: datetime


#Support Ticket Schemas
class SupportTicketCreate(BaseModel):
    """Create Support Ticket Request schema"""
    session_id: str
    customer_email: EmailStr
    issue_type: str
    priority: str = "medium"
    description: str

class SupportTicketResponse(BaseModel):
    """Response schema for Support Ticket endpoint"""
    ticket_id: str
    status: str
    created_at: datetime
    message: str


#Return Request Schemas
class ReturnRequestCreate(BaseModel):
    """Create Return Request schema"""
    session_id: str
    order_id: str
    customer_email: EmailStr
    reason: str
    notes: Optional[str] = None

class ReturnRequestResponse(BaseModel):
    """Response schema for Return endpoint"""
    request_id: str
    status: str
    created_at: datetime
    message: str


#Health Check Schemas
class HealthCheck(BaseModel):
    """Health check response schema"""
    status: str
    version: str
    timestamp: datetime
    database_status: str
    vector_db_status: str
