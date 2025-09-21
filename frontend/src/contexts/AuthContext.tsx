import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthCredentials {
    username: string;
    password: string;
}

interface AuthContextType {
    credentials: AuthCredentials | null;
    isAuthenticated: boolean;
    login: (username: string, password: string) => void;
    logout: () => void;
    getAuthHeaders: () => Record<string, string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [credentials, setCredentials] = useState<AuthCredentials | null>(null);

    // Check for stored credentials on initialization
    useEffect(() => {
        const storedCredentials = sessionStorage.getItem('auth-credentials');
        if (storedCredentials) {
            try {
                const parsed = JSON.parse(storedCredentials);
                setCredentials(parsed);
            } catch (error) {
                console.error('Error parsing stored credentials:', error);
                sessionStorage.removeItem('auth-credentials');
            }
        }
    }, []);

    const login = (username: string, password: string) => {
        const newCredentials = { username, password };
        setCredentials(newCredentials);
        // Store in sessionStorage (not localStorage for security)
        sessionStorage.setItem('auth-credentials', JSON.stringify(newCredentials));
    };

    const logout = () => {
        setCredentials(null);
        sessionStorage.removeItem('auth-credentials');
    };

    const getAuthHeaders = (): Record<string, string> => {
        if (!credentials) {
            return {
                'Content-Type': 'application/json',
            };
        }
        
        // Create Basic Auth header
        const basicAuth = btoa(`${credentials.username}:${credentials.password}`);
        return {
            'Authorization': `Basic ${basicAuth}`,
            'Content-Type': 'application/json',
        };
    };

    const isAuthenticated = credentials !== null;

    return (
        <AuthContext.Provider value={{
            credentials,
            isAuthenticated,
            login,
            logout,
            getAuthHeaders
        }}>
            {children}
        </AuthContext.Provider>
    );
};