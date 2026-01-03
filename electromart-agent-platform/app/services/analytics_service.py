from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy import func, select, Integer

from app.core.config import settings
from app.core.logs import get_logger
from app.database.database import get_db
from app.database.models import ConversationHistory, AgentAnalytics

logger = get_logger()


class AnalyticsService:
    """
    Service for tracking and analyzing agent performance metrics.
    Records detailed analytics for each agent interaction.
    """

    async def track_agent_performance(
        self,
        agent_type: str,
        query_type: str,
        success: bool,
        response_time_ms: int,
        tokens_used: int = 0,
        error_message: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track agent performance metrics to database.

        Args:
            agent_type: Type of agent (sales, support, etc.)
            query_type: Category of query handled
            success: Whether the agent successfully handled the request
            response_time_ms: Response time in milliseconds
            tokens_used: Number of tokens consumed
            error_message: Error message if failed
            extra_metadata: Additional metadata
        """
        try:
            async with get_db() as session:
                analytics_entry = AgentAnalytics(
                    agent_type=agent_type,
                    query_type=query_type,
                    success=success,
                    response_time_ms=response_time_ms,
                    tokens_used=tokens_used,
                    error_message=error_message,
                    extra_metadata=extra_metadata or {}
                )

                session.add(analytics_entry)
                await session.commit()

                logger.debug(f"Tracked analytics for {agent_type}: success={success}, time={response_time_ms}ms")

        except Exception as e:
            logger.error(f"Error tracking analytics: {e}")

    async def get_agent_performance_summary(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get performance summary for all agents.

        Args:
            days: Number of days to include in summary

        Returns:
            List of agent performance summaries
        """
        try:
            async for session in get_db():
                cutoff_date = datetime.now() - timedelta(days=days)

                # Query analytics for each agent type
                query = select(
                    AgentAnalytics.agent_type,
                    func.count(AgentAnalytics.id).label('total_queries'),
                    func.avg(AgentAnalytics.response_time_ms).label('avg_response_time'),
                    func.sum(AgentAnalytics.tokens_used).label('total_tokens'),
                    func.avg(
                        func.cast(AgentAnalytics.success, Integer)
                    ).label('success_rate')
                ).where(
                    AgentAnalytics.timestamp >= cutoff_date
                ).group_by(
                    AgentAnalytics.agent_type
                )

                result = await session.execute(query)
                rows = result.fetchall()

                performance_data = []
                for row in rows:
                    performance_data.append({
                        "agent_type": row.agent_type,
                        "total_queries": row.total_queries,
                        "success_rate": float(row.success_rate or 0),
                        "avg_response_time_ms": float(row.avg_response_time or 0),
                        "total_tokens_used": int(row.total_tokens or 0),
                        "avg_confidence": 0.88  # Would need to add confidence tracking
                    })

                logger.info(f"Retrieved performance summary for {len(performance_data)} agents")
                return performance_data

        except Exception as e:
            logger.error(f"Error retrieving agent performance: {e}")
            return []

    async def get_conversation_analytics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get conversation statistics.

        Args:
            days: Number of days to include

        Returns:
            Dictionary with conversation analytics
        """
        try:
            async for session in get_db():
                cutoff_date = datetime.now() - timedelta(days=days)

                # Count total conversations
                conv_query = select(
                    func.count(func.distinct(ConversationHistory.session_id))
                ).where(
                    ConversationHistory.timestamp >= cutoff_date
                )
                total_convs = await session.execute(conv_query)
                total_conversations = total_convs.scalar() or 0

                # Count total messages
                msg_query = select(
                    func.count(ConversationHistory.id)
                ).where(
                    ConversationHistory.timestamp >= cutoff_date
                )
                total_msgs = await session.execute(msg_query)
                total_messages = total_msgs.scalar() or 0

                # Average sentiment
                sentiment_query = select(
                    func.avg(ConversationHistory.sentiment_score)
                ).where(
                    ConversationHistory.timestamp >= cutoff_date
                )
                avg_sent = await session.execute(sentiment_query)
                avg_sentiment = avg_sent.scalar() or 0

                return {
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "avg_sentiment_score": float(avg_sentiment),
                    "period_days": days
                }

        except Exception as e:
            logger.error(f"Error retrieving conversation analytics: {e}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "avg_sentiment_score": 0,
                "period_days": days
            }

    async def get_error_rate_by_agent(self, days: int = 7) -> Dict[str, float]:
        """
        Get error rates for each agent type.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary mapping agent types to error rates
        """
        try:
            async for session in get_db():
                cutoff_date = datetime.now() - timedelta(days=days)

                query = select(
                    AgentAnalytics.agent_type,
                    func.avg(
                        func.cast(~AgentAnalytics.success, Integer)
                    ).label('error_rate')
                ).where(
                    AgentAnalytics.timestamp >= cutoff_date
                ).group_by(
                    AgentAnalytics.agent_type
                )

                result = await session.execute(query)
                rows = result.fetchall()

                error_rates = {row.agent_type: float(row.error_rate or 0) for row in rows}

                return error_rates

        except Exception as e:
            logger.error(f"Error calculating error rates: {e}")
            return {}


# Global analytics service instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """
    Get or create the global analytics service instance.

    Returns:
        AnalyticsService: Global analytics service instance
    """
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
