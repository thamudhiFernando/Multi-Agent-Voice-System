/**
 * ChatInterface component - Main chat UI with message input and display.
 * Handles message sending, loading states, and conversation management.
 *
 * Features:
 * - Real-time message display with user and assistant messages
 * - Voice input support using Web Speech API
 * - Auto-scrolling to latest messages
 * - Suggestion chips for follow-up questions
 * - Session management with unique IDs
 * - Error handling and loading states
 */

'use client';

// React core imports
import React, { useState, useRef, useEffect } from 'react';

// Material-UI component imports
import {
    Box,          // Container component for layout
    Button,       // Clickable button component
    Typography,   // Text display component
    Alert,        // Alert/notification component
    IconButton,   // Button with icon only
} from '@mui/material';

// Material-UI icon imports
import MicIcon from '@mui/icons-material/Mic';    // Microphone icon for voice input
import SendIcon from '@mui/icons-material/Send';  // Send icon for message submission

// External library imports
import { v4 as uuidv4 } from 'uuid';  // UUID generator for session IDs

// Local component and utility imports
import {ChatMessage} from "@/components/ChatMessage/ChatMessage";
import {ChatResponse, Message} from "@/types/types";// TypeScript type definitions
import { api } from '@/api/api';             // API client for backend communication

// Styles import
import styles from './ChatInterface.module.scss';

export const ChatInterface: React.FC = () => {
    // ==================== STATE MANAGEMENT ====================

    // Array of all chat messages (user and assistant)
    const [messages, setMessages] = useState<Message[]>([]);

    // Current value of the text input field
    const [inputValue, setInputValue] = useState('');

    // Loading state indicator for message sending
    const [isLoading, setIsLoading] = useState(false);

    // Unique session ID for the current conversation
    const [sessionId, setSessionId] = useState<string>('');

    // Error message to display (null if no error)
    const [error, setError] = useState<string | null>(null);

    // Array of suggested follow-up questions from the assistant
    const [suggestions, setSuggestions] = useState<string[]>([]);

    // Flag indicating if voice recording is active
    const [isRecording, setIsRecording] = useState(false);

    // Speech recognition instance (Web Speech API)
    const [recognition, setRecognition] = useState<any>(null);

    // ==================== REFS ====================

    // Reference to the bottom of messages container for auto-scrolling
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Reference to the textarea input for focus management
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // ==================== LIFECYCLE EFFECTS ====================

    /**
     * Effect: Initialize session on component mount
     * Creates a unique session ID for tracking the conversation
     * Runs once when the component first renders
     */
    useEffect(() => {
        const newSessionId = uuidv4();
        setSessionId(newSessionId);
        console.log('Session initialized:', newSessionId);
    }, []);

    /**
     * Effect: Auto-scroll to bottom when messages change
     * Ensures the latest message is always visible
     * Runs whenever the messages array is updated
     */
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    /**
     * Effect: Focus input field on component mount
     * Provides better UX by immediately allowing user to type
     * Runs once when the component first renders
     */
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    /**
     * Effect: Initialize speech recognition API
     * Sets up Web Speech API for voice input functionality
     * Configures event handlers for speech recognition results and errors
     * Runs once when the component first renders
     */
    useEffect(() => {
        // Check if running in browser environment
        if (typeof window !== 'undefined') {
            // Get SpeechRecognition API (with webkit prefix for Safari)
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

            if (SpeechRecognition) {
                // Create new recognition instance
                const recognitionInstance = new SpeechRecognition();

                // Configure recognition settings
                recognitionInstance.continuous = false;      // Stop after one result
                recognitionInstance.interimResults = false;  // Only return final results
                recognitionInstance.lang = 'en-US';         // Set language to English (US)

                /**
                 * Handler: Speech recognition result received
                 * Extracts the transcript and updates the input field
                 */
                recognitionInstance.onresult = (event: any) => {
                    const transcript = event.results[0][0].transcript;
                    setInputValue(transcript);
                    setIsRecording(false);
                };

                /**
                 * Handler: Speech recognition error occurred
                 * Displays error message and stops recording
                 */
                recognitionInstance.onerror = (event: any) => {
                    console.error('Speech recognition error:', event.error);
                    setError('Voice recognition error. Please try again.');
                    setIsRecording(false);
                };

                /**
                 * Handler: Speech recognition ended
                 * Updates recording state when recognition stops
                 */
                recognitionInstance.onend = () => {
                    setIsRecording(false);
                };

                // Save recognition instance to state
                setRecognition(recognitionInstance);
            }
        }
    }, []);

    // ==================== EVENT HANDLERS ====================

    /**
     * Handler: Send message to backend
     *
     * Flow:
     * 1. Validates input is not empty and not already loading
     * 2. Displays user message immediately (optimistic UI update)
     * 3. Sends message to backend API
     * 4. Displays assistant response when received
     * 5. Updates suggestion chips for follow-up questions
     * 6. Handles errors by removing user message and showing error
     *
     * @async
     */
    const handleSendMessage = async () => {
        // Guard: Prevent sending empty messages or sending while loading
        if (!inputValue.trim() || isLoading) return;

        // Store and clear the message
        const userMessage = inputValue.trim();
        setInputValue('');
        setError(null);

        // Create user message object
        const userMsg: Message = {
            role: 'user',
            content: userMessage,
            timestamp: new Date().toISOString(),
        };

        // Add user message to UI immediately (optimistic update)
        setMessages((prev) => [...prev, userMsg]);

        // Set loading state to show spinner
        setIsLoading(true);

        try {
            // Send message to backend API
            const response: ChatResponse = await api.sendMessage({
                message: userMessage,
                session_id: sessionId,
            });

            // Create assistant message object from response
            const assistantMsg: Message = {
                role: 'assistant',
                content: response.response,
                timestamp: response.timestamp,
                agent_type: response.agent_info.agent_type,
            };

            // Add assistant response to messages
            setMessages((prev) => [...prev, assistantMsg]);

            // Update suggestion chips if provided
            if (response.suggestions) {
                setSuggestions(response.suggestions);
            }

            // Log response details for debugging
            console.log('Response received:', {
                agent: response.agent_info.agent_type,
                confidence: response.agent_info.confidence,
                time: response.response_time_ms + 'ms',
            });
        } catch (err) {
            // Log error to console
            console.error('Error sending message:', err);

            // Display error message to user
            setError('Failed to send message. Please try again.');

            // Remove optimistic user message on error (rollback)
            setMessages((prev) => prev.slice(0, -1));
        } finally {
            // Always clean up: remove loading state and refocus input
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    /**
     * Handler: Suggestion chip clicked
     * Populates the input field with the selected suggestion
     * and focuses the input for user to edit or send
     *
     * @param suggestion - The suggested question text to populate
     */
    const handleSuggestionClick = (suggestion: string) => {
        // Set the suggestion as the input value
        setInputValue(suggestion);

        // Focus the input so user can immediately edit or send
        inputRef.current?.focus();
    };

    /**
     * Handler: Clear chat conversation
     *
     * Flow:
     * 1. Calls backend API to clear conversation history
     * 2. Clears local messages and suggestions
     * 3. Generates new session ID for fresh conversation
     * 4. Handles any errors silently (logs to console)
     *
     * @async
     */
    const handleClearChat = async () => {
        // Guard: Only proceed if session ID exists
        if (sessionId) {
            try {
                // Call backend to clear conversation history
                await api.clearConversation(sessionId);

                // Clear local state
                setMessages([]);
                setSuggestions([]);
                setError(null);

                // Generate new session ID for fresh conversation
                const newSessionId = uuidv4();
                setSessionId(newSessionId);

                console.log('Chat cleared, new session:', newSessionId);
            } catch (err) {
                // Log error but don't show to user (non-critical operation)
                console.error('Error clearing chat:', err);
            }
        }
    };

    /**
     * Handler: Toggle voice input recording
     *
     * Flow:
     * 1. Checks if speech recognition is supported
     * 2. If recording: stops recognition
     * 3. If not recording: starts recognition
     * 4. Handles errors during start/stop
     *
     * Uses Web Speech API to convert voice to text
     */
    const handleVoiceInput = () => {
        // Guard: Check if speech recognition is available
        if (!recognition) {
            setError('Voice recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
            return;
        }

        // Toggle recording state
        if (isRecording) {
            // Stop recording
            recognition.stop();
            setIsRecording(false);
        } else {
            // Start recording
            setError(null);
            setIsRecording(true);

            try {
                // Start speech recognition
                recognition.start();
            } catch (err) {
                // Handle errors (e.g., microphone permission denied)
                console.error('Error starting recognition:', err);
                setIsRecording(false);
                setError('Failed to start voice recognition. Please try again.');
            }
        }
    };

    // ==================== RENDER ====================

    return (
        <Box className={styles.chatContainer}>
            {/* ==================== HEADER SECTION ==================== */}
            {/* Contains title, subtitle, and clear chat button */}
            <Box className={styles.header}>
                <Box className={styles.headerContent}>
                    {/* Title and subtitle */}
                    <Box className={styles.headerText}>
                        <Typography variant="h2" component="h2">
                            ElectroMart Assistant
                        </Typography>
                        <Typography component="p">
                            How can I help you today?
                        </Typography>
                    </Box>

                    {/* Clear chat button */}
                    <Button
                        onClick={handleClearChat}
                        className={styles.clearButton}
                        variant="text"
                    >
                        Clear Chat
                    </Button>
                </Box>
            </Box>

            {/* ==================== MESSAGES SECTION ==================== */}
            {/* Scrollable container for all messages and states */}
            <Box className={styles.messagesContainer}>
                {/* Welcome screen - shown when no messages exist */}
                {messages.length === 0 && (
                    <Box className={styles.welcomeSection}>
                        {/* Welcome icon */}
                        <Box className={styles.welcomeIcon}>🛍️</Box>

                        {/* Welcome title */}
                        <Typography variant="h3" component="h3">
                            Welcome to ElectroMart!
                        </Typography>

                        {/* Welcome description */}
                        <Typography component="p">
                            I'm your AI assistant. Ask me about products, orders, promotions,
                            technical support, or general inquiries.
                        </Typography>

                        {/* Example question buttons to help users get started */}
                        <Box className={styles.exampleButtons}>
                            {[
                                "What's the price of iPhone 15 Pro?",
                                'Do you have any ongoing promotions?',
                                'Track my order #12345',
                                'My laptop won\'t turn on',
                            ].map((example) => (
                                <Button
                                    key={example}
                                    onClick={() => setInputValue(example)}
                                    className={styles.exampleButton}
                                    variant="text"
                                >
                                    {example}
                                </Button>
                            ))}
                        </Box>
                    </Box>
                )}

                {/* Render all chat messages (user and assistant) */}
                {messages.map((message, index) => (
                    <ChatMessage key={index} message={message} />
                ))}

                {/* Loading indicator - animated dots shown while waiting for response */}
                {isLoading && (
                    <Box className={styles.loadingIndicator}>
                        <Box className={styles.loadingDots}>
                            <Box className={styles.dot} />
                            <Box className={styles.dot} />
                            <Box className={styles.dot} />
                        </Box>
                    </Box>
                )}

                {/* Error alert - shown when message sending fails */}
                {error && (
                    <Alert severity="error" className={styles.errorAlert}>
                        {error}
                    </Alert>
                )}

                {/* Invisible div at the bottom for auto-scrolling */}
                <div ref={messagesEndRef} />
            </Box>

            {/* ==================== SUGGESTIONS SECTION ==================== */}
            {/* Follow-up question suggestions from assistant - shown when available and not loading */}
            {suggestions.length > 0 && !isLoading && (
                <Box className={styles.suggestionsSection}>
                    {/* Suggestions label */}
                    <Typography component="p">Suggested questions:</Typography>

                    {/* Suggestion chip buttons */}
                    <Box className={styles.suggestionButtons}>
                        {suggestions.map((suggestion, index) => (
                            <Button
                                key={index}
                                onClick={() => handleSuggestionClick(suggestion)}
                                className={styles.suggestionButton}
                                variant="outlined"
                            >
                                {suggestion}
                            </Button>
                        ))}
                    </Box>
                </Box>
            )}

            {/* ==================== INPUT SECTION ==================== */}
            {/* Message input area with textarea, voice button, and send button */}
            <Box className={styles.inputSection}>
                <Box className={styles.inputContainer}>
                    {/* Text input wrapper */}
                    <Box className={styles.textareaWrapper}>
            <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                    // Send message on Enter, allow new line on Shift+Enter
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                    }
                }}
                placeholder={isRecording ? "Listening..." : "Type or speak your message... (Shift+Enter for new line)"}
                rows={1}
                className={styles.textarea}
                disabled={isLoading || isRecording}
            />
                    </Box>

                    {/* Voice input button - toggles speech recognition */}
                    <IconButton
                        onClick={handleVoiceInput}
                        disabled={isLoading}
                        className={`${styles.voiceButton} ${isRecording ? styles.recording : styles.notRecording}`}
                        title={isRecording ? 'Stop recording' : 'Start voice input'}
                    >
                        <MicIcon />
                    </IconButton>

                    {/* Send message button */}
                    <Button
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isLoading}
                        className={`${styles.sendButton} ${!inputValue.trim() || isLoading ? styles.disabled : styles.active}`}
                        variant="contained"
                        disableElevation
                        endIcon={<SendIcon />}
                    >
                        {isLoading ? 'Sending...' : 'Send'}
                    </Button>
                </Box>

                {/* Footer text - shows recording status or branding */}
                <Typography className={styles.footerText}>
                    {isRecording ? '🎙️ Recording... Speak now' : 'Ready... Type now'}
                </Typography>
            </Box>
        </Box>
    );
};
