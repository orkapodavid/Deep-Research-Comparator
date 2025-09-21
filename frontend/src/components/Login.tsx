import React, { useState } from 'react';
import { colors } from '../config/colors';

interface LoginProps {
    onLogin: (username: string, password: string) => Promise<boolean>;
    error?: string;
}

export const Login: React.FC<LoginProps> = ({ onLogin, error }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [loginError, setLoginError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!username.trim() || !password.trim()) {
            setLoginError('Please enter both username and password');
            return;
        }

        setIsLoading(true);
        setLoginError(null);

        try {
            const success = await onLogin(username.trim(), password);
            if (!success) {
                setLoginError('Invalid username or password');
            }
        } catch (error) {
            setLoginError('Login failed. Please try again.');
            console.error('Login error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const displayError = loginError || error;

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#F9F7F7]">
            <div className="max-w-md w-full space-y-8 p-8">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-bold" style={{ color: colors.primary }}>
                        Deep Research Comparator
                    </h2>
                    <p className="mt-2 text-center text-sm text-gray-600">
                        Please sign in to access the application
                    </p>
                </div>
                
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="username" className="sr-only">
                                Username
                            </label>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:z-10 sm:text-sm"
                                style={{ 
                                    borderColor: colors.secondary
                                }}
                                placeholder="Username"
                                disabled={isLoading}
                            />
                        </div>
                        
                        <div>
                            <label htmlFor="password" className="sr-only">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:z-10 sm:text-sm"
                                style={{ 
                                    borderColor: colors.secondary
                                }}
                                placeholder="Password"
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    {displayError && (
                        <div className="text-red-600 text-sm text-center">
                            {displayError}
                        </div>
                    )}

                    <div>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            style={{ 
                                backgroundColor: colors.secondary
                            }}
                        >
                            {isLoading ? (
                                <div className="flex items-center">
                                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                                    Signing in...
                                </div>
                            ) : (
                                'Sign in'
                            )}
                        </button>
                    </div>
                </form>

                <div className="text-xs text-gray-500 text-center">
                    <p>Default credentials: admin / password</p>
                    <p className="mt-1">Contact administrator for access credentials</p>
                </div>
            </div>
        </div>
    );
};