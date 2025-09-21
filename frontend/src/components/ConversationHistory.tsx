import { useState, useEffect } from 'react';
import { colors } from '../config/colors';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAuth } from '../contexts/AuthContext';

interface Agent {
    id: string;
    name: string;
    response: string;
    intermediate_steps?: string;
    citations?: string;
}

interface Conversation {
    id: string;
    session_id: string;
    timestamp: string;
    question: string;
    agents: Agent[];
}

interface PaginationInfo {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
}

export const ConversationHistory = () => {
    const { getAuthHeaders } = useAuth();
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [pagination, setPagination] = useState<PaginationInfo>({
        page: 1,
        page_size: 10,
        total_count: 0,
        total_pages: 0
    });
    const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

    useEffect(() => {
        fetchConversations(1);
    }, []);

    const fetchConversations = async (page: number) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(
                `${import.meta.env.VITE_API_BASE_URL}/api/conversation-history?page=${page}&page_size=10`,
                {
                    method: 'GET',
                    headers: getAuthHeaders(),
                }
            );
            
            // Handle authentication errors
            if (response.status === 401) {
                setError('Authentication required. Please log in again.');
                return;
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                setConversations(data.conversations);
                setPagination(data.pagination);
            } else {
                setError('Failed to fetch conversations');
            }
        } catch (err) {
            setError('Error loading conversations: ' + (err as Error).message);
        } finally {
            setLoading(false);
        }
    };

    const handlePageChange = (newPage: number) => {
        if (newPage >= 1 && newPage <= pagination.total_pages) {
            fetchConversations(newPage);
        }
    };

    const formatTimestamp = (timestamp: string) => {
        return new Date(timestamp).toLocaleString();
    };

    const truncateText = (text: string, maxLength: number = 100) => {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-lg">Loading conversations...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-red-600 text-lg">{error}</div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto p-4">
            <h1 className="text-3xl font-bold mb-6" style={{ color: colors.primary }}>
                Conversation History
            </h1>
            
            {conversations.length === 0 ? (
                <div className="text-center py-8">
                    <p className="text-gray-600 text-lg">No conversations found.</p>
                    <p className="text-gray-500 mt-2">Start a conversation to see the history here.</p>
                </div>
            ) : (
                <>
                    {/* Conversation List */}
                    <div className="space-y-4 mb-8">
                        {conversations.map((conversation) => (
                            <div
                                key={conversation.id}
                                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                                style={{ borderColor: colors.secondary }}
                                onClick={() => setSelectedConversation(conversation)}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="text-lg font-semibold" style={{ color: colors.primary }}>
                                        {truncateText(conversation.question, 80)}
                                    </h3>
                                    <span className="text-sm text-gray-500">
                                        {formatTimestamp(conversation.timestamp)}
                                    </span>
                                </div>
                                
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                                    {conversation.agents.map((agent, index) => (
                                        <div key={index} className="bg-gray-50 p-3 rounded">
                                            <div className="font-medium text-sm mb-2" style={{ color: colors.secondary }}>
                                                {agent.name}
                                            </div>
                                            <div className="text-sm text-gray-700">
                                                {truncateText(agent.response)}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Pagination */}
                    {pagination.total_pages > 1 && (
                        <div className="flex justify-center items-center space-x-4">
                            <button
                                onClick={() => handlePageChange(pagination.page - 1)}
                                disabled={pagination.page === 1}
                                className="px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                                style={{ 
                                    backgroundColor: pagination.page === 1 ? '#ccc' : colors.secondary,
                                    color: '#fff'
                                }}
                            >
                                Previous
                            </button>
                            
                            <span className="text-sm text-gray-600">
                                Page {pagination.page} of {pagination.total_pages} 
                                ({pagination.total_count} total conversations)
                            </span>
                            
                            <button
                                onClick={() => handlePageChange(pagination.page + 1)}
                                disabled={pagination.page === pagination.total_pages}
                                className="px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                                style={{ 
                                    backgroundColor: pagination.page === pagination.total_pages ? '#ccc' : colors.secondary,
                                    color: '#fff'
                                }}
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            )}

            {/* Conversation Detail Modal */}
            {selectedConversation && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-5xl max-h-[90vh] overflow-y-auto w-[90vw]">
                        <div className="flex justify-between items-start mb-4">
                            <h2 className="text-2xl font-bold" style={{ color: colors.primary }}>
                                Conversation Details
                            </h2>
                            <button
                                onClick={() => setSelectedConversation(null)}
                                className="text-gray-500 hover:text-gray-700 text-2xl"
                            >
                                ×
                            </button>
                        </div>
                        
                        <div className="mb-6">
                            <div className="text-sm text-gray-500 mb-2">
                                {formatTimestamp(selectedConversation.timestamp)}
                            </div>
                            <div className="text-lg font-semibold mb-4" style={{ color: colors.secondary }}>
                                Question: {selectedConversation.question}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {selectedConversation.agents.map((agent, index) => (
                                <div key={index} className="border rounded-lg p-4" style={{ borderColor: colors.secondary }}>
                                    <h3 className="text-lg font-semibold mb-3" style={{ color: colors.primary }}>
                                        {agent.name}
                                    </h3>
                                    
                                    {agent.intermediate_steps && (
                                        <div className="mb-4">
                                            <h4 className="font-medium text-sm mb-2 text-gray-700">Thinking Process:</h4>
                                            <div className="text-sm bg-gray-50 p-3 rounded max-h-40 overflow-y-auto">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {agent.intermediate_steps}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    )}
                                    
                                    <div className="mb-4">
                                        <h4 className="font-medium text-sm mb-2 text-gray-700">Response:</h4>
                                        <div className="text-sm max-h-60 overflow-y-auto">
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {agent.response}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                    
                                    {agent.citations && (
                                        <div>
                                            <h4 className="font-medium text-sm mb-2 text-gray-700">Citations:</h4>
                                            <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                                                {agent.citations}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};