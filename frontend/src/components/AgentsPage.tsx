import { useState, useEffect } from 'react';
import { QuestionInput } from './QuestionInput';
import { SessionData, ChatHistory, ChatMessage, AgentInfo } from '../types';
import { colors } from '../config/colors';
import { streamAgentsResponse } from '../utils/streamingAgents.ts';
import { DeepResearchChatContainer } from './ChatContainer.tsx';
import { useAuth } from '../contexts/AuthContext';

export const AgentsPage = () => {
    const { getAuthHeaders } = useAuth();
    const [sessionData, setSessionData] = useState<SessionData>({
        sessionId: null,
        currentQuestion: '',
        selectedChoice: '',
        selectedAgents: [],
    });
    const [agentInfo, setAgentInfo] = useState<AgentInfo[]>([]);
    const [isQuestionDisabled, setIsQuestionDisabled] = useState(true);
    const [conversationHistory, setConversationHistory] = useState<{
        agentA: ChatHistory;
        agentB: ChatHistory;
        agentC: ChatHistory;
    }>({
        agentA: { messages: [] },
        agentB: { messages: [] },
        agentC: { messages: [] }
    });

    useEffect(() => {
        initializeAgents();
    }, []);

    const initializeAgents = async () => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/deepresearch-agents`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            });
            const data = await response.json();

            if (data.error) {
                console.error('Error fetching agents:', data.error);
                return;
            }

            // Store agent/embedding info in state
            setSessionData(prev => ({ 
                ...prev, 
                selectedAgents: data.agents,
                sessionId: data.session_id,
            }));
            setAgentInfo(data.agents);
            setIsQuestionDisabled(false);
            setConversationHistory({
                agentA: { messages: [] },
                agentB: { messages: [] },
                agentC: { messages: [] }
            });
        } catch (error) {
            console.error('Error fetching agents:', error);
        }
    };
    
    const handleQuestionSubmit = async (question: string) => {
        setIsQuestionDisabled(true);
        try {
            // Add user message to all conversation histories
            const userMessage: ChatMessage = {
                role: 'user',
                content: [{ text: question }]
            };

            // Add user message to conversation histories first
            setConversationHistory(prev => {
                // Create initial empty assistant messages
                const agentAMessage: ChatMessage = {
                    role: 'assistant',
                    content: [{ text: '' }],
                    intermediate_steps: '',
                    is_intermediate: true
                };
                const agentBMessage: ChatMessage = {
                    role: 'assistant',
                    content: [{ text: '' }],
                    intermediate_steps: '',
                    is_intermediate: true
                };
                const agentCMessage: ChatMessage = {
                    role: 'assistant',
                    content: [{ text: '' }],
                    intermediate_steps: '',
                    is_intermediate: true
                };

                const newState = {
                    agentA: {
                        messages: [...prev.agentA.messages, userMessage, agentAMessage]
                    },
                    agentB: {
                        messages: [...prev.agentB.messages, userMessage, agentBMessage]
                    },
                    agentC: {
                        messages: [...prev.agentC.messages, userMessage, agentCMessage]
                    }
                };

                return newState;
            });
            
            // Prepare payload for three agents
            const payload = {
                question,
                conversation_a: conversationHistory.agentA.messages,
                conversation_b: conversationHistory.agentB.messages,
                conversation_c: conversationHistory.agentC.messages,
            };
            
            // Start streaming the response
            await streamAgentsResponse(
                `${import.meta.env.VITE_API_BASE_URL}/api/deepresearch-question`,
                payload,
                (chunk) => {                    
                    // Ensure chunk is not null or undefined
                    if (!chunk) {
                        console.error('Received null/undefined chunk');
                        return;
                    }
                    
                    // Update agent A content only if it was updated in this chunk
                    if (chunk.agentA_updated) {                        
                        setConversationHistory(prev => {
                            const agentAMessages = [...prev.agentA.messages];
                            const assistantMsgIndex = agentAMessages.length - 1;
                            if (assistantMsgIndex >= 0) {
                                const assistantMsg = { ...agentAMessages[assistantMsgIndex] };
                                
                                assistantMsg.content = [{ text: chunk.agentA.content || '' }];
                                if (chunk.agentA.intermediate) {
                                    assistantMsg.intermediate_steps = chunk.agentA.intermediate;
                                } else if (assistantMsg.intermediate_steps === undefined) {
                                    assistantMsg.intermediate_steps = '';
                                }
                                if (chunk.agentA.citations) {
                                    assistantMsg.citations = chunk.agentA.citations;
                                }
                                assistantMsg.is_intermediate = chunk.agentA_is_intermediate;
                                assistantMsg.is_complete = chunk.agentA_is_complete;

                                agentAMessages[assistantMsgIndex] = assistantMsg;
                            }
                            return { ...prev, agentA: { messages: agentAMessages } };
                        });
                    }
                    
                    // Update agent B content only if it was updated in this chunk
                    if (chunk.agentB_updated) {                        
                        setConversationHistory(prev => {
                            const agentBMessages = [...prev.agentB.messages];
                            const assistantMsgIndex = agentBMessages.length - 1;
                            if (assistantMsgIndex >= 0) {
                                const assistantMsg = { ...agentBMessages[assistantMsgIndex] };

                                assistantMsg.content = [{ text: chunk.agentB.content || '' }];
                                if (chunk.agentB.intermediate) {
                                    assistantMsg.intermediate_steps = chunk.agentB.intermediate;
                                } else if (assistantMsg.intermediate_steps === undefined) {
                                    assistantMsg.intermediate_steps = '';
                                }
                                if (chunk.agentB.citations) {
                                    assistantMsg.citations = chunk.agentB.citations;
                                }
                                assistantMsg.is_intermediate = chunk.agentB_is_intermediate;
                                assistantMsg.is_complete = chunk.agentB_is_complete;
                                
                                agentBMessages[assistantMsgIndex] = assistantMsg;
                            }
                            return { ...prev, agentB: { messages: agentBMessages } };
                        });
                    }
                    
                    // Update agent C content only if it was updated in this chunk
                    if (chunk.agentC_updated) {                        
                        setConversationHistory(prev => {
                            const agentCMessages = [...prev.agentC.messages];
                            const assistantMsgIndex = agentCMessages.length - 1;
                            if (assistantMsgIndex >= 0) {
                                const assistantMsg = { ...agentCMessages[assistantMsgIndex] };

                                assistantMsg.content = [{ text: chunk.agentC.content || '' }];
                                if (chunk.agentC.intermediate) {
                                    assistantMsg.intermediate_steps = chunk.agentC.intermediate;
                                } else if (assistantMsg.intermediate_steps === undefined) {
                                    assistantMsg.intermediate_steps = '';
                                }
                                if (chunk.agentC.citations) {
                                    assistantMsg.citations = chunk.agentC.citations;
                                }
                                assistantMsg.is_intermediate = chunk.agentC_is_intermediate;
                                assistantMsg.is_complete = chunk.agentC_is_complete;
                                
                                agentCMessages[assistantMsgIndex] = assistantMsg;
                            }
                            return { ...prev, agentC: { messages: agentCMessages } };
                        });
                    }
                    
                    // If this is the final chunk, save the conversation
                    if (chunk.is_final) {
                        // Save the conversation automatically
                        saveConversation(question);
                    }
                },
                getAuthHeaders()
            );

            console.log('Streaming complete');
            setSessionData(prev => ({ ...prev, currentQuestion: question }));

        } catch (error) {
            console.error('Error in handleQuestionSubmit:', error);
        }
    };

    const saveConversation = async (question: string) => {
        try {
            if (!sessionData.sessionId || !agentInfo.length || agentInfo.length < 3) {
                console.log('Not enough data to save conversation');
                return;
            }

            // Get the latest responses from conversation history
            const agentAMessages = conversationHistory.agentA.messages;
            const agentBMessages = conversationHistory.agentB.messages;
            const agentCMessages = conversationHistory.agentC.messages;
            
            // Find the latest assistant messages
            const latestAgentAResponse = agentAMessages
                .filter(msg => msg.role === 'assistant')
                .pop();
            const latestAgentBResponse = agentBMessages
                .filter(msg => msg.role === 'assistant')
                .pop();
            const latestAgentCResponse = agentCMessages
                .filter(msg => msg.role === 'assistant')
                .pop();
            
            if (!latestAgentAResponse || !latestAgentBResponse || !latestAgentCResponse) {
                console.log('Not all agent responses available for saving');
                return;
            }

            const payload = {
                session_id: sessionData.sessionId,
                question: question,
                agent_a_id: agentInfo[0].agent_id,
                agent_a_name: agentInfo[0].name,
                agent_a_response: latestAgentAResponse.content[0]?.text || '',
                agent_a_intermediate_steps: latestAgentAResponse.intermediate_steps || '',
                agent_a_citations: JSON.stringify(latestAgentAResponse.citations || []),
                agent_b_id: agentInfo[1].agent_id,
                agent_b_name: agentInfo[1].name,
                agent_b_response: latestAgentBResponse.content[0]?.text || '',
                agent_b_intermediate_steps: latestAgentBResponse.intermediate_steps || '',
                agent_b_citations: JSON.stringify(latestAgentBResponse.citations || []),
                agent_c_id: agentInfo[2].agent_id,
                agent_c_name: agentInfo[2].name,
                agent_c_response: latestAgentCResponse.content[0]?.text || '',
                agent_c_intermediate_steps: latestAgentCResponse.intermediate_steps || '',
                agent_c_citations: JSON.stringify(latestAgentCResponse.citations || [])
            };

            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/save-conversation`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            if (data.status === 'success') {
                console.log('Conversation saved successfully');
            } else {
                console.error('Failed to save conversation:', data);
            }
        } catch (error) {
            console.error('Error saving conversation:', error);
        }
    };

    const handleNewRound = () => {
        window.location.reload();
    };

    return (
        <div className="w-full">
            <div className="pt-4 grid grid-cols-1 md:grid-cols-3 gap-2">
                {/* Agent A */}
                <div className="flex flex-col space-y-4 pl-4">
                    <h2 className="text-2xl font-bold text-center">{agentInfo[0]?.name || 'Agent A'}</h2>
                    <DeepResearchChatContainer
                        history={conversationHistory.agentA}
                        agentId="agentA"
                        agentUuid={agentInfo[0]?.id}
                        sessionId={sessionData.sessionId ?? undefined}
                    />
                </div>

                {/* Agent B */}
                <div className="flex flex-col space-y-4 px-2">
                    <h2 className="text-2xl font-bold text-center">{agentInfo[1]?.name || 'Agent B'}</h2>
                    <DeepResearchChatContainer
                        history={conversationHistory.agentB}
                        agentId="agentB"
                        agentUuid={agentInfo[1]?.id}
                        sessionId={sessionData.sessionId ?? undefined}
                    />
                </div>

                {/* Agent C */}
                <div className="flex flex-col space-y-4 pr-4">
                    <h2 className="text-2xl font-bold text-center">{agentInfo[2]?.name || 'Agent C'}</h2>
                    <DeepResearchChatContainer
                        history={conversationHistory.agentC}
                        agentId="agentC"
                        agentUuid={agentInfo[2]?.id}
                        sessionId={sessionData.sessionId ?? undefined}
                    />
                </div>
            </div>

            <div className="mt-8 space-y-4 max-w-4xl mx-auto">
                <QuestionInput
                    onSubmit={handleQuestionSubmit}
                    disabled={isQuestionDisabled}
                />
                
                <div className="text-center text-gray-600">
                    Compare responses from the three different LLM agents above
                </div>
                
                <div className="flex justify-center mt-8">
                    <button
                        onClick={handleNewRound}
                        style={{ backgroundColor: colors.secondary }}
                        className="px-4 py-2 text-[#F9F7F7] rounded-md hover:bg-[#213555] focus:outline-none focus:ring-2 focus:ring-[#213555] focus:ring-offset-2 disabled:opacity-50"
                        disabled={isQuestionDisabled}
                    >
                        Start New Round
                    </button>
                </div>
            </div>
        </div>
    );
};