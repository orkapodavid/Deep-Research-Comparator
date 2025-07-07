import { useState, useEffect } from 'react';
import { QuestionInput } from './QuestionInput';
import { ChoiceButtons } from './ChoiceButtons';
import { DeepResearchAgentDetails } from './AgentDetails.tsx';
import { SessionData, ChoiceType, ChatHistory, ChatMessage } from '../types';
import { colors } from '../config/colors';
import { streamResponse } from '../utils/streaming.ts';
import { DeepResearchChatContainer } from './ChatContainer.tsx';

interface AgentInfo {
    name: string;
    id: string;
}

export const DeepResearchPage = () => {
    const [sessionData, setSessionData] = useState<SessionData>({
        sessionId: null,
        currentQuestion: '',
        selectedChoice: '',
        selectedAgents: [],
    });
    const [agentDetails, setAgentDetails] = useState<{ AgentA: AgentInfo | null, AgentB: AgentInfo | null }>({
        AgentA: null,
        AgentB: null,
    });
    const [isQuestionDisabled, setIsQuestionDisabled] = useState(true);
    const [isChoiceDisabled, setIsChoiceDisabled] = useState(true);
    const [hasAnswered, setHasAnswered] = useState(false);
    const [conversationHistory, setConversationHistory] = useState<{
        agentA: ChatHistory;
        agentB: ChatHistory;
    }>({
        agentA: { messages: [] },
        agentB: { messages: [] }
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

            // Store agent/embedding info in state, but we'll send it with each request
            setSessionData(prev => ({ 
                ...prev, 
                selectedAgents: data.agents,
                sessionId: data.session_id,
            }));
            setIsQuestionDisabled(false);
            setIsChoiceDisabled(true);
            setAgentDetails({ AgentA: null, AgentB: null });
            setHasAnswered(false);
            setConversationHistory({
                agentA: { messages: [] },
                agentB: { messages: [] }
            });
        } catch (error) {
            console.error('Error fetching agents:', error);
        }
    };
    
    const handleQuestionSubmit = async (question: string) => {
        setIsQuestionDisabled(true);
        try {
            // Add user message to both conversation histories
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
                    intermediate: '',
                    isIntermediate: true
                };
                const agentBMessage: ChatMessage = {
                    role: 'assistant',
                    content: [{ text: '' }],
                    intermediate: '',
                    isIntermediate: true
                };

                const newState = {
                    agentA: {
                        messages: [...prev.agentA.messages, userMessage, agentAMessage]
                    },
                    agentB: {
                        messages: [...prev.agentB.messages, userMessage, agentBMessage]
                    }
                };

                return newState;
            });
            
            // Prepare payload with conversation history and agent info
            const payload = {
                question,
                conversation_a: conversationHistory.agentA.messages,
                conversation_b: conversationHistory.agentB.messages,
                selected_agents: {
                    agentA: sessionData.selectedAgents?.[0]?.id,
                    agentB: sessionData.selectedAgents?.[1]?.id
                }
            };
            
            // Start streaming the response
            await streamResponse(
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
                                
                                // The backend now sends agentA.content (final) and agentA.intermediate (think) separately
                                // The agentA_isIntermediate flag indicates which phase the agent is in.
                                assistantMsg.content = [{ text: chunk.agentA.content || '' }];
                                // Only update intermediate if new intermediate content is provided, preserve existing intermediate otherwise
                                if (chunk.agentA.intermediate) {
                                    assistantMsg.intermediate = chunk.agentA.intermediate;
                                } else if (assistantMsg.intermediate === undefined) {
                                    assistantMsg.intermediate = '';
                                }
                                if (chunk.agentA.citations) {
                                    assistantMsg.citations = chunk.agentA.citations;
                                }
                                assistantMsg.isIntermediate = chunk.agentA_isIntermediate;
                                assistantMsg.isComplete = chunk.agentA_complete;

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

                                // The backend now sends agentB.content (final) and agentB.intermediate (think) separately
                                // The agentB_isIntermediate flag indicates which phase the agent is in.
                                assistantMsg.content = [{ text: chunk.agentB.content || '' }];
                                // Only update intermediate if new intermediate content is provided, preserve existing intermediate otherwise
                                if (chunk.agentB.intermediate) {
                                    assistantMsg.intermediate = chunk.agentB.intermediate;
                                } else if (assistantMsg.intermediate === undefined) {
                                    assistantMsg.intermediate = '';
                                }
                                if (chunk.agentB.citations) {
                                    assistantMsg.citations = chunk.agentB.citations;
                                }
                                assistantMsg.isIntermediate = chunk.agentB_isIntermediate;
                                assistantMsg.isComplete = chunk.agentB_complete;
                                
                                agentBMessages[assistantMsgIndex] = assistantMsg;
                            }
                            return { ...prev, agentB: { messages: agentBMessages } };
                        });
                    }
                    
                    // If this is the final chunk, enable the choice buttons
                    if (chunk.final) {
                        setIsChoiceDisabled(false);
                        setHasAnswered(false);
                    }

                    if (chunk.metadata) {
                        const metadata = chunk.metadata as any;
                        if (metadata.selected_agents) {
                        }
                    }
                }
            );

            console.log('Streaming complete');
            setSessionData(prev => ({ ...prev, currentQuestion: question }));

        } catch (error) {
            console.error('Error in handleQuestionSubmit:', error);
        }
    };

    const handleChoice = async (choice: ChoiceType) => {
        try {
            // Send all state to the backend in a stateless way
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/deepresearch-choice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    choice,
                    question : sessionData.currentQuestion,
                    conversation_a: conversationHistory.agentA.messages,
                    conversation_b: conversationHistory.agentB.messages,
                    selected_agents: sessionData.selectedAgents,
                    session_id: sessionData.sessionId,
                }),
            });
            const data = await response.json();

            if (data.error) {
                console.error('Error:', data.error);
                return;
            }

            // Update agent details with the response data
            setAgentDetails({
                AgentA: data.AgentA || null,
                AgentB: data.AgentB || null,
            });
            setIsQuestionDisabled(true);
            setIsChoiceDisabled(true);
            setHasAnswered(true);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    const handleNewRound = () => {
        window.location.reload();
    };

    return (
        <div className="w-full">
            <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-2">
                {/* Agent A */}
                <div className="flex flex-col space-y-4 pl-4">
                    <h2 className="text-2xl font-bold text-center">Agent A</h2>
                    <DeepResearchChatContainer
                        history={conversationHistory.agentA}
                        agentId="agentA"
                        agentUuid={sessionData.selectedAgents?.[0]?.id}
                        sessionId={sessionData.sessionId ?? undefined}
                    />
                </div>

                {/* Agent B */}
                <div className="flex flex-col space-y-4 pr-4">
                    <h2 className="text-2xl font-bold text-center">Agent B</h2>
                    <DeepResearchChatContainer
                        history={conversationHistory.agentB}
                        agentId="agentB"
                        agentUuid={sessionData.selectedAgents?.[1]?.id}
                        sessionId={sessionData.sessionId ?? undefined}
                    />
                </div>
            </div>

            <div className="mt-8 space-y-4 max-w-4xl mx-auto">
                <QuestionInput
                    onSubmit={handleQuestionSubmit}
                    disabled={isQuestionDisabled}
                />
                <ChoiceButtons
                    onChoice={handleChoice}
                    disabled={isChoiceDisabled}
                    hasAnswered={hasAnswered}
                />
                {hasAnswered && (
                    <div className="mt-4">
                        <DeepResearchAgentDetails details={agentDetails} />
                    </div>
                )}
                <div className="flex justify-center mt-8">
                    <button
                        onClick={handleNewRound}
                        style={{ backgroundColor: colors.secondary }}
                        className="px-4 py-2 text-[#F9F7F7] rounded-md hover:bg-[#213555] focus:outline-none focus:ring-2 focus:ring-[#213555] focus:ring-offset-2 disabled:opacity-50"
                        disabled={isChoiceDisabled && !hasAnswered}
                    >
                        Start New Round
                    </button>
                </div>
            </div>
        </div>
    );
};
