from sqlalchemy import Column, Integer, DateTime, String, func, Text, Float, JSON, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ConversationHistory(Base):
    """
    Stores conversation history for context management and analytics.
    """
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), index=True, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    agent_type = Column(String(100), nullable=False)  # orchestrator, sales, support, etc.
    intent_detected = Column(String(100))
    confidence_score = Column(Float)
    sentiment_score = Column(Float)
    sentiment_label = Column(String(50))  # positive, negative, neutral
    response_time_ms = Column(Integer)  # Response time in milliseconds
    extra_metadata = Column(JSON)  # Additional context data


class AgentAnalytics(Base):
    """
    Tracks agent performance metrics for monitoring and optimization.
    """
    __tablename__ = "agent_analytics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    agent_type = Column(String(100), nullable=False)
    query_type = Column(String(100))
    success = Column(Boolean, default=True)
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    error_message = Column(Text, nullable=True)
    user_feedback = Column(Integer, nullable=True)  # 1-5 rating
    extra_metadata = Column(JSON)


class SupportTicket(Base):
    """
    Tracks support tickets created during conversations.
    """
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(String(100), unique=True, index=True, nullable=False)
    session_id = Column(String(255), index=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    customer_email = Column(String(255))
    issue_type = Column(String(100), nullable=False)
    priority = Column(String(50), default="medium")  # low, medium, high, urgent
    status = Column(String(50), default="open")  # open, in_progress, resolved, closed
    description = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    assigned_agent = Column(String(100))
    extra_metadata = Column(JSON)


class ReturnRequest(Base):
    """
    Manages return/refund requests initiated through the system.
    """
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(String(100), unique=True, index=True, nullable=False)
    session_id = Column(String(255), index=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    order_id = Column(String(100), nullable=False)
    customer_email = Column(String(255), nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")  # pending, approved, rejected, completed
    refund_amount = Column(Float)
    notes = Column(Text)
    extra_metadata = Column(JSON)


class UserFeedback(Base):
    """
    Collects user feedback on agent responses for continuous improvement.
    """
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), index=True, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    feedback_text = Column(Text)
    agent_type = Column(String(100), nullable=False)
    helpful = Column(Boolean)
    extra_metadata = Column(JSON)
