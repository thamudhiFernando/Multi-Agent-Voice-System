import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.agents.crew_agents import get_agent_coordinator
from app.core.config import settings
from app.core.logs import get_logger
from app.knowledge_base.vector_store import get_vector_store
from app.schemas.schemas import ChatResponse, ChatRequest, AgentInfo, SentimentInfo, HealthCheck, SystemAnalytics, \
    FeedbackRequest
from app.services.analytics_service import get_analytics_service
from app.services.conversation_service import get_conversation_service
from app.services.humain_escalation_service import get_escalation_service
from app.services.sentiment_service import get_sentiment_service

logger = get_logger()

#Create Router
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def create_chat(
        request: ChatRequest,
        background_tasks: BackgroundTasks
) :
    start_time = time.time()

    try:
        #Generate session ID if it not provide
        session_id = request.session_id or str(uuid.uuid4())

        #Get Services
        conversation_service =  get_conversation_service()
        agent_coordinator = get_agent_coordinator()
        escalation_service = get_escalation_service()
        sentiment_service = get_sentiment_service()
        analytics_service = get_analytics_service()

        logger.debug(f"Processing chat req for session : {session_id}")

        #Add user message to conversation history
        conversation_service.create_message(
            session_id = session_id,
            role= "user",
            content= request.message
        )

        # Add user message to conversation history
        conversation_service.create_message(
            session_id = session_id,
            role= "user",
            content= request.message
        )

        # Analyze sentiment
        sentiment_analysis = sentiment_service.analyze_customer_emotion(request.message)

        #Get conversation context
        context = conversation_service.get_conversation_context_for_agent(session_id, max_turns = 5)
        conversation_length = len(conversation_service.get_conversation_history(session_id))

        # Check if customer escalation is needed
        should_escalate, escalation_reason, priority =  await escalation_service.should_escalate_to_customer(
            sentiment_analysis = sentiment_analysis,
            conversation_length = conversation_length,
        )

        #Classify intent using orchestrator
        agent_type, confidence = agent_coordinator.classify_intent(
            message = request.message,
            conversation_context = context,
        )

        #Process with specialized agent
        success = True
        error_msg = None
        try:
            response_text = agent_coordinator.process_with_agent(
                agent_type = agent_type,
                message = request.message,
                conversation_context = context
            )
        except Exception as e:
            success = False
            error_msg = str(e)
            response_text = "I apologize, but I encountered an error processing your request. Please try again."
            logger.error(f"Error occurred with agent : {e}")

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Create support ticket if escalation needed
        ticket_id = None
        if should_escalate:
            try:
                ticket_id = await escalation_service.create_support_ticket(
                    session_id = session_id,
                    customer_email = request.customer_email if hasattr(request, "customer_email") else None,
                    issue_type = agent_type,
                    description = f"Automated Escalation: {escalation_reason}\n\nUser message: {request.message}",
                    priority = priority,
                    extra_metadata = {
                        "sentiment": sentiment_analysis,
                        "conversation_length": conversation_length,
                        "escalation_reason": escalation_reason,
                    }
                )
                logger.info(f"Escalation ticket: {ticket_id} created for session : {session_id}")

                # Add escalation notice to response
                response_text += f"\n\n⚠️ Your case has been escalated to our human support team (Ticket #{ticket_id}). A representative will assist you shortly. "

            except Exception as e:
                logger.error(f"Error occurred with support ticket : {e}")

        # Add response of assistant to conversation history
        conversation_service.create_message(
            session_id = session_id,
            role= "assistant",
            content= response_text,
            agent_type= agent_type,
            metadata={
                "confidence": confidence,
                "sentiment": sentiment_analysis,
                "escalated": should_escalate,
                "ticket_id": ticket_id
            }
        )

        # Track analytics in background
        background_tasks.add_task(
            analytics_service.track_agent_performance,
            agent_type=agent_type,
            query_type=sentiment_analysis.get("label", "unknown"),
            success=success,
            response_time_ms=response_time_ms,
            tokens_used=0,  # Would need to track actual tokens from OpenAI
            error_message=error_msg,
            extra_metadata={
                "confidence": confidence,
                "escalated": should_escalate
            }
        )

        # Persist conversation to database in background
        background_tasks.add_task(
            conversation_service.persist_conversation,
            session_id=session_id,
            user_message=request.message,
            agent_response=response_text,
            agent_type=agent_type,
            intent_detected=agent_type,
            confidence_score=confidence,
            sentiment_score=sentiment_analysis.get("score"),
            sentiment_label=sentiment_analysis.get("label"),
            response_time_ms=response_time_ms,
            extra_metadata={
                "escalated": should_escalate,
                "ticket_id": ticket_id
            }
        )

        # Prepare response
        response = ChatResponse(
            response=response_text,
            session_id=session_id,
            agent_info=AgentInfo(
                agent_type=agent_type,
                confidence=confidence
            ),
            sentiment=SentimentInfo(
                label=sentiment_analysis["label"],
                score=sentiment_analysis["score"]
            ) if settings.ENABLE_SENTIMENT_ANALYSIS else None,
            response_time_ms=response_time_ms,
            timestamp=datetime.now(),
            suggestions=_generate_suggestions(agent_type)
        )

        logger.info(f"Chat request processed successfully in {response_time_ms}ms")

        # Schedule background cleanup
        background_tasks.add_task(conversation_service.cleanup_expired_sessions)

        return response

    except Exception as e:
        logger.error(f"Error: processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat request: {str(e)}")


@router.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """
    Get conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        Conversation history with all messages
    """
    try:
        conversation_service = get_conversation_service()
        messages = conversation_service.get_conversation_history(session_id)

        return {
            "session_id": session_id,
            "messages": messages,
            "total_messages": len(messages)
        }

    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")


@router.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """
    Clear conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        Success message
    """
    try:
        conversation_service = get_conversation_service()
        conversation_service.clear_session(session_id)

        return {"message": f"Conversation {session_id} cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback on agent responses.

    Args:
        request: Feedback request with rating and comments

    Returns:
        Success message
    """
    try:
        logger.info(f"Feedback received for session {request.session_id}: {request.rating}/5")

        # In a production system, this would save to database
        # For now, just log it

        return {
            "message": "Thank you for your feedback!",
            "session_id": request.session_id
        }

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@router.get("/analytics", response_model=SystemAnalytics)
async def get_analytics(days: int = 7):
    """
    Get system analytics and performance metrics.

    Args:
        days: Number of days to include in analytics (default: 7)

    Returns:
        System analytics with agent performance data
    """
    try:
        analytics_service = get_analytics_service()

        # Get conversation analytics from database
        conversation_stats = await analytics_service.get_conversation_analytics(days=days)

        # Get agent performance from database
        agent_performance = await analytics_service.get_agent_performance_summary(days=days)

        return SystemAnalytics(
            total_conversations=conversation_stats.get("total_conversations", 0),
            total_messages=conversation_stats.get("total_messages", 0),
            avg_sentiment_score=conversation_stats.get("avg_sentiment_score", 0),
            agent_performance=agent_performance,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error retrieving analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics: {str(e)}")


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint for monitoring system status.

    Returns:
        Health check response with system status
    """
    try:
        # Check vector store
        vector_store = get_vector_store()
        vector_db_status = "healthy" if vector_store.get_collection_count("products") > 0 else "unhealthy"

        return HealthCheck(
            status="healthy",
            version=settings.APP_VERSION,
            timestamp=datetime.now(),
            database_status="healthy",
            vector_db_status=vector_db_status
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            version=settings.APP_VERSION,
            timestamp=datetime.now(),
            database_status="unknown",
            vector_db_status="unknown"
        )


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """
    Get support ticket by ID.

    Args:
        ticket_id: Ticket identifier

    Returns:
        Ticket details
    """
    try:
        escalation_service = get_escalation_service()
        ticket = await escalation_service.get_ticket_by_id(ticket_id)

        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

        return ticket

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving ticket: {str(e)}")


@router.get("/tickets/session/{session_id}")
async def get_tickets_by_session(session_id: str):
    """
    Get all support tickets for a session.

    Args:
        session_id: Session identifier

    Returns:
        List of tickets for the session
    """
    try:
        escalation_service = get_escalation_service()
        tickets = await escalation_service.get_tickets_by_session(session_id)

        return {
            "session_id": session_id,
            "tickets": tickets,
            "total_tickets": len(tickets)
        }

    except Exception as e:
        logger.error(f"Error retrieving tickets for session: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tickets: {str(e)}")


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    status: Optional[str] = None,
    resolution: Optional[str] = None,
    assigned_agent: Optional[str] = None
):
    """
    Update support ticket status.

    Args:
        ticket_id: Ticket identifier
        status: New status (open, in_progress, resolved, closed)
        resolution: Resolution notes
        assigned_agent: Assigned human agent

    Returns:
        Success message
    """
    try:
        escalation_service = get_escalation_service()

        await escalation_service.update_ticket_status(
            ticket_id=ticket_id,
            status=status,
            resolution=resolution,
            assigned_agent=assigned_agent
        )

        return {
            "message": f"Ticket {ticket_id} updated successfully",
            "ticket_id": ticket_id
        }

    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")


def _generate_suggestions(agent_type: str) -> List[str]:
    suggestions_map = {
        "sales": [
            "Can you compare this with similar products?",
            "Are there any bundles or accessories available?",
            "What's the warranty on this product?"
        ],
        "marketing": [
            "How do I join the loyalty program?",
            "Are there any upcoming sales?",
            "Can I combine multiple discount codes?"
        ],
        "technical_support": [
            "What if this doesn't solve my problem?",
            "How do I check my warranty status?",
            "Can I schedule a repair appointment?"
        ],
        "order_logistics": [
            "Can I change my delivery address?",
            "How do I track my package?",
            "What's your return policy?"
        ],
        "customer_service": [
            "What are your store hours?",
            "Do you offer price matching?",
            "How can I contact customer support?"
        ]
    }

    return suggestions_map.get(agent_type, [
        "How can I track my order?",
        "What promotions are currently active?",
        "Tell me about your return policy"
    ])