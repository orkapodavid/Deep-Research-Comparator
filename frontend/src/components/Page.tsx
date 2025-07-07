import { useState, useEffect } from 'react';
import { QuestionInput } from './QuestionInput';
import { ChoiceButtons } from './ChoiceButtons';
import { DeepResearchModelDetails } from './AgentDetails.tsx';
import { SessionData, ChoiceType, ChatHistory, ChatMessage } from '../types';
import { colors } from '../config/colors';
import { streamResponse } from '../utils/streaming.ts';
import { DeepResearchChatContainer } from './ChatContainer.tsx';

interface ModelInfo {
    name: string;
    id: string;
}

export const DeepResearchPage = () => {
    const [sessionData, setSessionData] = useState<SessionData>({
        sessionId: null,
        currentQuestion: '',
        selectedChoice: '',
        selectedModels: [],
    });
    const [modelDetails, setModelDetails] = useState<{ ModelA: ModelInfo | null, ModelB: ModelInfo | null }>({
        ModelA: null,
        ModelB: null,
    });
    const [isQuestionDisabled, setIsQuestionDisabled] = useState(true);
    const [isChoiceDisabled, setIsChoiceDisabled] = useState(true);
    const [hasAnswered, setHasAnswered] = useState(false);
    const [conversationHistory, setConversationHistory] = useState<{
        modelA: ChatHistory;
        modelB: ChatHistory;
    }>({
        modelA: { messages: [] },
        modelB: { messages: [] }
    });

    useEffect(() => {
        initializeModels();
    }, []);

    const initializeModels = async () => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/deepresearch-models`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            });
            const data = await response.json();

            if (data.error) {
                console.error('Error fetching models:', data.error);
                return;
            }

            // Store model/embedding info in state, but we'll send it with each request
            setSessionData(prev => ({ 
                ...prev, 
                selectedModels: data.models,
                sessionId: data.session_id,
            }));
            setIsQuestionDisabled(false);
            setIsChoiceDisabled(true);
            setModelDetails({ ModelA: null, ModelB: null });
            setHasAnswered(false);
            setConversationHistory({
                modelA: { messages: [] },
                modelB: { messages: [] }
            });
        } catch (error) {
            console.error('Error fetching models:', error);
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
                const modelAMessage: ChatMessage = {
                    role: 'assistant',
                    content: [{ text: '' }],
                    reasoning: '',
                    isReasoning: true
                };
                const modelBMessage: ChatMessage = {
                    role: 'assistant',
                    content: [{ text: '' }],
                    reasoning: '',
                    isReasoning: true
                };

                const newState = {
                    modelA: {
                        messages: [...prev.modelA.messages, userMessage, modelAMessage]
                    },
                    modelB: {
                        messages: [...prev.modelB.messages, userMessage, modelBMessage]
                    }
                };

                return newState;
            });
            
            // Prepare payload with conversation history and model info
            const payload = {
                question,
                conversation_a: conversationHistory.modelA.messages,
                conversation_b: conversationHistory.modelB.messages,
                selected_models: {
                    modelA: sessionData.selectedModels?.[0]?.id,
                    modelB: sessionData.selectedModels?.[1]?.id
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
                    
                    // Update model A content only if it was updated in this chunk
                    if (chunk.modelA_updated) {                        
                        setConversationHistory(prev => {
                            const modelAMessages = [...prev.modelA.messages];
                            const assistantMsgIndex = modelAMessages.length - 1;
                            if (assistantMsgIndex >= 0) {
                                const assistantMsg = { ...modelAMessages[assistantMsgIndex] };
                                
                                // The backend now sends modelA.content (final) and modelA.reasoning (think) separately
                                // The modelA_isReasoning flag indicates which phase the model is in.
                                assistantMsg.content = [{ text: chunk.modelA.content || '' }];
                                // Only update reasoning if new reasoning content is provided, preserve existing reasoning otherwise
                                if (chunk.modelA.reasoning) {
                                    assistantMsg.reasoning = chunk.modelA.reasoning;
                                } else if (assistantMsg.reasoning === undefined) {
                                    assistantMsg.reasoning = '';
                                }
                                if (chunk.modelA.citations) {
                                    assistantMsg.citations = chunk.modelA.citations;
                                }
                                assistantMsg.isReasoning = chunk.modelA_isReasoning;
                                assistantMsg.isComplete = chunk.modelA_complete;

                                modelAMessages[assistantMsgIndex] = assistantMsg;
                            }
                            return { ...prev, modelA: { messages: modelAMessages } };
                        });
                    }
                    
                    // Update model B content only if it was updated in this chunk
                    if (chunk.modelB_updated) {                        
                        setConversationHistory(prev => {
                            const modelBMessages = [...prev.modelB.messages];
                            const assistantMsgIndex = modelBMessages.length - 1;
                            if (assistantMsgIndex >= 0) {
                                const assistantMsg = { ...modelBMessages[assistantMsgIndex] };

                                // The backend now sends modelB.content (final) and modelB.reasoning (think) separately
                                // The modelB_isReasoning flag indicates which phase the model is in.
                                assistantMsg.content = [{ text: chunk.modelB.content || '' }];
                                // Only update reasoning if new reasoning content is provided, preserve existing reasoning otherwise
                                if (chunk.modelB.reasoning) {
                                    assistantMsg.reasoning = chunk.modelB.reasoning;
                                } else if (assistantMsg.reasoning === undefined) {
                                    assistantMsg.reasoning = '';
                                }
                                if (chunk.modelB.citations) {
                                    assistantMsg.citations = chunk.modelB.citations;
                                }
                                assistantMsg.isReasoning = chunk.modelB_isReasoning;
                                assistantMsg.isComplete = chunk.modelB_complete;
                                
                                modelBMessages[assistantMsgIndex] = assistantMsg;
                            }
                            return { ...prev, modelB: { messages: modelBMessages } };
                        });
                    }
                    
                    // If this is the final chunk, enable the choice buttons
                    if (chunk.final) {
                        setIsChoiceDisabled(false);
                        setHasAnswered(false);
                    }

                    if (chunk.metadata) {
                        const metadata = chunk.metadata as any;
                        if (metadata.selected_models) {
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
                    conversation_a: conversationHistory.modelA.messages,
                    conversation_b: conversationHistory.modelB.messages,
                    selected_models: sessionData.selectedModels,
                    session_id: sessionData.sessionId,
                }),
            });
            const data = await response.json();

            if (data.error) {
                console.error('Error:', data.error);
                return;
            }

            // Update model details with the response data
            setModelDetails({
                ModelA: data.ModelA || null,
                ModelB: data.ModelB || null,
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
                {/* Model A */}
                <div className="flex flex-col space-y-4 pl-4">
                    <h2 className="text-2xl font-bold text-center">Agent A</h2>
                    <DeepResearchChatContainer
                        history={conversationHistory.modelA}
                        modelId="modelA"
                        modelUuid={sessionData.selectedModels?.[0]?.id}
                        sessionId={sessionData.sessionId ?? undefined}
                    />
                </div>

                {/* Model B */}
                <div className="flex flex-col space-y-4 pr-4">
                    <h2 className="text-2xl font-bold text-center">Agent B</h2>
                    <DeepResearchChatContainer
                        history={conversationHistory.modelB}
                        modelId="modelB"
                        modelUuid={sessionData.selectedModels?.[1]?.id}
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
                        <DeepResearchModelDetails details={modelDetails} />
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
