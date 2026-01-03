/**
 * Main page component for the ElectroMart Multi-Agent System frontend.
 * Displays the chat interface and handles the main application layout.
 */

'use client';

import { Box, AppBar, Container, Typography, Button, Paper } from '@mui/material';
import { ChatInterface } from '@/components/ChatInterface/ChatInterface';
import styles from './page.module.scss';

export default function Home() {
    return (
        <Box className={styles.mainContainer}>
            {/* Navigation bar */}
            <AppBar position="static" className={styles.navbar} elevation={0}>
                <Container className={styles.navbarContainer} maxWidth={false}>
                    <Box className={styles.navbarContent}>
                        <Box className={styles.logoSection}>
                            <Box className={styles.logo}>🛍️</Box>
                            <Box className={styles.logoText}>
                                <Typography variant="h1" component="h1">
                                    ElectroMart
                                </Typography>
                                <Typography variant="body2" component="p">
                                    AI Customer Assistant
                                </Typography>
                            </Box>
                        </Box>
                        <Box className={styles.navActions}>
                            <Button
                                href="/analytics"
                                className={styles.analyticsButton}
                                variant="contained"
                                disableElevation
                            >
                                Analytics
                            </Button>
                        </Box>
                    </Box>
                </Container>
            </AppBar>

            {/* Main content */}
            <Container className={styles.contentContainer} maxWidth={false}>
                <Paper className={styles.chatCard} elevation={3}>
                    <ChatInterface />
                </Paper>
            </Container>

            {/* Footer */}
            <Box component="footer" className={styles.footer}>
                <Box className={styles.footerContent}>
                    <Typography component="p">
                        ElectroMart Multi-Agent System v1.0.0
                    </Typography>
                    <Typography component="p" className="subtitle">
                        Powered by GPT-4
                    </Typography>
                </Box>
            </Box>
        </Box>
    );
}
