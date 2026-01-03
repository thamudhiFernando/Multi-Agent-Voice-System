/**
 * API client for communicating with the backend FastAPI server.
 * Handles all HTTP requests and response parsing.
 */

import axios, { AxiosInstance } from 'axios';
import {
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    FeedbackRequest,
    HealthCheck,
    SystemAnalytics
} from "@/types/types";


const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Axios instance with default configuration
 */
const apiClient: AxiosInstance = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 seconds
});

/**
 * API client class with methods for all backend endpoints
 */
class APIClient {
    /**
     * Send a chat message to the backend
     */
    async sendMessage(request: ChatRequest): Promise<ChatResponse> {
        const response = await apiClient.post<ChatResponse>('/chat', request);
        return response.data;
    }

    /**
     * Get conversation history for a session
     */
    async getConversation(sessionId: string): Promise<ConversationHistory> {
        const response = await apiClient.get<ConversationHistory>(
            `/conversation/${sessionId}`
        );
        return response.data;
    }

    /**
     * Clear conversation history for a session
     */
    async clearConversation(sessionId: string): Promise<void> {
        await apiClient.delete(`/conversation/${sessionId}`);
    }

    /**
     * Submit user feedback
     */
    async submitFeedback(request: FeedbackRequest): Promise<void> {
        await apiClient.post('/feedback', request);
    }

    /**
     * Get system analytics
     */
    async getAnalytics(): Promise<SystemAnalytics> {
        const response = await apiClient.get<SystemAnalytics>('/analytics');
        return response.data;
    }

    /**
     * Check system health
     */
    async healthCheck(): Promise<HealthCheck> {
        const response = await apiClient.get<HealthCheck>('/health');
        return response.data;
    }
}

// Export singleton instance
export const api = new APIClient();

// Export axios instance for custom requests
export { apiClient };
