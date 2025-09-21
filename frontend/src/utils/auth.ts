import { useAuth } from '../contexts/AuthContext';

/**
 * Custom hook for making authenticated API requests
 */
export const useAuthenticatedFetch = () => {
    const { getAuthHeaders } = useAuth();

    const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
        const authHeaders = getAuthHeaders();
        
        const requestOptions: RequestInit = {
            ...options,
            headers: {
                ...authHeaders,
                ...options.headers,
            },
        };

        return fetch(url, requestOptions);
    };

    return authenticatedFetch;
};

/**
 * Test authentication credentials by making a request to a protected endpoint
 */
export const testAuthentication = async (username: string, password: string): Promise<boolean> => {
    try {
        const basicAuth = btoa(`${username}:${password}`);
        const headers = {
            'Authorization': `Basic ${basicAuth}`,
            'Content-Type': 'application/json',
        };

        // Test with the agents endpoint (non-protected) to verify server connectivity first
        const testResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/deepresearch-agents`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!testResponse.ok) {
            console.error('Cannot connect to backend server');
            return false;
        }

        // Test authentication with a protected endpoint
        const authResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/conversation-history?page=1&page_size=1`, {
            method: 'GET',
            headers,
        });

        // If we get 401, credentials are wrong
        // If we get 200, credentials are correct
        // Other errors might be server issues
        if (authResponse.status === 401) {
            return false;
        }

        if (authResponse.status === 200) {
            return true;
        }

        // For other status codes, log and return false
        console.error('Unexpected response status:', authResponse.status);
        return false;

    } catch (error) {
        console.error('Authentication test failed:', error);
        return false;
    }
};