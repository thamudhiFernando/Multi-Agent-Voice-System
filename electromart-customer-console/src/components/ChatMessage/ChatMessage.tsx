/**
 * ChatMessage component displays individual messages in the chat interface.
 * Styles differ based on whether the message is from user or assistant.
 */

import React from 'react';
import { Box, Typography } from '@mui/material';
import { formatDistanceToNow } from 'date-fns';
import styles from './ChatMessage.module.scss';
import {AgentType, Message} from "@/types/types";

interface ChatMessageProps {
    message: Message;
}

/**
 * Get agent icon and style class based on agent type
 */
const getAgentStyle = (agentType?: AgentType) => {
    const agentStyles = {
        sales: { icon: '🛒', className: 'sales', label: 'Sales' },
        marketing: { icon: '🎯', className: 'marketing', label: 'Marketing' },
        technical_support: { icon: '🔧', className: 'technicalSupport', label: 'Tech Support' },
        order_logistics: { icon: '📦', className: 'orderLogistics', label: 'Orders' },
        customer_service: { icon: '💬', className: 'customerService', label: 'Customer Service' },
        orchestrator: { icon: '🎭', className: 'orchestrator', label: 'System' },
    };

    return agentStyles[agentType as AgentType] || agentStyles.customer_service;
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    const isUser = message.role === 'user';
    const agentStyle = !isUser ? getAgentStyle(message.agent_type) : null;

    // Format timestamp
    const timeAgo = formatDistanceToNow(new Date(message.timestamp), { addSuffix: true });

    return (
        <Box className={`${styles.messageContainer} ${isUser ? styles.user : styles.assistant}`}>
            <Box className={`${styles.messageWrapper} ${isUser ? styles.user : styles.assistant}`}>
                {/* Agent badge for assistant messages */}
                {!isUser && agentStyle && (
                    <Box className={styles.agentBadgeContainer}>
                        <Box className={`${styles.agentBadge} ${styles[agentStyle.className]}`}>
                            <span className={styles.icon}>{agentStyle.icon}</span>
                            {agentStyle.label}
                        </Box>
                        <Typography className={styles.timestamp}>{timeAgo}</Typography>
                    </Box>
                )}

                {/* Message content */}
                <Box className={`${styles.messageContent} ${isUser ? styles.user : styles.assistant}`}>
                    <p>{message.content}</p>
                </Box>

                {/* Timestamp for user messages */}
                {isUser && (
                    <Box className={styles.timestampContainer}>
                        <Typography className={styles.timestamp}>{timeAgo}</Typography>
                    </Box>
                )}
            </Box>
        </Box>
    );
};
