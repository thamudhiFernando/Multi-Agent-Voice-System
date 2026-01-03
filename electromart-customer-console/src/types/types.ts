/**
 * TypeScript type definitions for the ElectroMart frontend.
 * Matches backend Pydantic schemas for type safety.
 */

export interface ChatRequest {
    message: string;
    session_id?: string;
    voice_input?: boolean;
}

export interface AgentInfo {
    agent_type: AgentType;
    confidence: number;
}

export interface SentimentInfo {
    label: SentimentLabel;
    score: number;
}

export interface ChatResponse {
    response: string;
    session_id: string;
    agent_info: AgentInfo;
    sentiment?: SentimentInfo;
    response_time_ms: number;
    timestamp: string;
    suggestions?: string[];
}

export interface Message {
    role: MessageRole;
    content: string;
    timestamp: string;
    agent_type?: AgentType;
}

export interface ConversationHistory {
    session_id: string;
    messages: Message[];
    total_messages: number;
}

export interface FeedbackRequest {
    session_id: string;
    rating: number;
    feedback_text?: string;
    helpful: boolean;
}

export interface HealthCheck {
    status: string;
    version: string;
    timestamp: string;
    database_status: string;
    vector_db_status: string;
}

export interface AgentPerformance {
    agent_type: AgentType;
    total_queries: number;
    success_rate: number;
    avg_response_time_ms: number;
    avg_confidence: number;
    total_tokens_used: number;
}

export interface SystemAnalytics {
    total_conversations: number;
    total_messages: number;
    avg_sentiment_score: number;
    agent_performance: AgentPerformance[];
    timestamp: string;
}

// Enums
export type MessageRole = 'user' | 'assistant' | 'system';

export type AgentType =
    | 'orchestrator'
    | 'sales'
    | 'marketing'
    | 'technical_support'
    | 'order_logistics'
    | 'customer_service';

export type SentimentLabel = 'positive' | 'negative' | 'neutral';

// UI State Types
export interface ChatState {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
    sessionId: string | null;
}
