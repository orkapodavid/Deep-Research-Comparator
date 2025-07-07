import { ChatHistory } from '../types';
import { DeepResearchChatMessage } from './ChatMessage';
import { colors } from '../config/colors';

interface DeepResearchChatContainerProps {
    history: ChatHistory;
    modelId: 'modelA' | 'modelB';
    modelUuid?: string;
    sessionId?: string;
}

export const DeepResearchChatContainer = ({ 
    history, 
    modelId, 
    modelUuid,
    sessionId,
}: DeepResearchChatContainerProps) => {
    return (
        <div className={`flex flex-col h-[500px] overflow-y-auto p-4 bg-[${colors.background}] rounded-lg border border-[${colors.secondary}]`}>
            {history.messages.map((message, index) => (
                <div key={`message-${index}`} className="mb-6">
                    <DeepResearchChatMessage 
                        message={message} 
                        modelId={modelId} 
                        modelUuid={modelUuid}
                        sessionId={sessionId}
                    />
                </div>
            ))}
        </div>
    );
}; 