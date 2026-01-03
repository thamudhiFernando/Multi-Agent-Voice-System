/**
 * MUI Theme configuration for ElectroMart application
 */

import { createTheme } from '@mui/material/styles';

const theme = createTheme({
    palette: {
        primary: {
            main: '#2563eb', // primary-600
            light: '#3b82f6', // primary-500
            dark: '#1e40af', // primary-700
            contrastText: '#ffffff',
        },
        secondary: {
            main: '#64748b', // gray-500
            light: '#94a3b8', // gray-400
            dark: '#475569', // gray-600
            contrastText: '#ffffff',
        },
        error: {
            main: '#ef4444',
            light: '#fef2f2',
            dark: '#dc2626',
        },
        warning: {
            main: '#f97316',
            light: '#ffedd5',
            dark: '#ea580c',
        },
        info: {
            main: '#3b82f6',
            light: '#dbeafe',
            dark: '#2563eb',
        },
        success: {
            main: '#22c55e',
            light: '#dcfce7',
            dark: '#16a34a',
        },
        grey: {
            50: '#f9fafb',
            100: '#f3f4f6',
            200: '#e5e7eb',
            300: '#d1d5db',
            400: '#9ca3af',
            500: '#6b7280',
            600: '#4b5563',
            700: '#374151',
            800: '#1f2937',
            900: '#111827',
        },
        background: {
            default: '#f9fafb',
            paper: '#ffffff',
        },
        text: {
            primary: '#111827',
            secondary: '#6b7280',
            disabled: '#9ca3af',
        },
    },
    typography: {
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        h1: {
            fontSize: '2rem',
            fontWeight: 700,
            lineHeight: 1.2,
        },
        h2: {
            fontSize: '1.5rem',
            fontWeight: 600,
            lineHeight: 1.3,
        },
        h3: {
            fontSize: '1.25rem',
            fontWeight: 600,
            lineHeight: 1.4,
        },
        body1: {
            fontSize: '0.875rem',
            lineHeight: 1.5,
        },
        body2: {
            fontSize: '0.75rem',
            lineHeight: 1.5,
        },
        button: {
            textTransform: 'none',
            fontWeight: 500,
        },
    },
    shape: {
        borderRadius: 8,
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: '0.5rem',
                    padding: '0.5rem 1.5rem',
                    transition: 'all 0.2s',
                },
                contained: {
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: 'none',
                    },
                },
            },
        },
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        borderRadius: '0.5rem',
                    },
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    borderRadius: '0.75rem',
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    borderRadius: '9999px',
                },
            },
        },
    },
});

export default theme;
