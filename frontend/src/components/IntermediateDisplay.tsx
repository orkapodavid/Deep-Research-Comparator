import { useState } from 'react';
import { colors } from '../config/colors';
import { PerplexityIntermediateStep } from './IntermediateStep';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface IntermediateDisplayProps {
    intermediateText: string;
    agentId: 'agentA' | 'agentB' | 'agentC';
    isIntermediate?: boolean;
    agentUuid?: string;
    sessionId?: string;
}

export const IntermediateDisplay = ({ intermediateText, agentId, isIntermediate = false, agentUuid, sessionId }: IntermediateDisplayProps) => {
    const [isCollapsed, setIsCollapsed] = useState(true);

    if (!intermediateText) {
        console.log('No intermediate text provided');
        return null;
    }
    console.log('agentUuid', agentUuid);
    console.log('intermediateText', intermediateText);
    const intermediateSteps: string[] = intermediateText
        .split(/\|\|\|---\|\|\|/g)
        .map(step => step.trim())
        .filter(step => step !== '');

    console.log('intermediateSteps:', intermediateSteps);

    const getIntermediatePreview = () => {
        if (intermediateSteps.length === 0) {
            return "";
        }

        const lastThreeSteps = intermediateSteps.slice(-3);
        const previewText = lastThreeSteps.map(step => step.trim()).join('\n');
        return previewText.length > 200 ? `...${previewText.slice(-200)}` : previewText;
    }

    return (
        <div className={`p-2 border border-solid border-[#b8cbdb] rounded-md bg-[${colors.light}]`}>
            <button 
                onClick={() => setIsCollapsed(!isCollapsed)}
                className={`w-full text-left px-2 py-1 text-sm font-medium text-[${colors.secondary}] hover:bg-[${colors.light}] rounded-md focus:outline-none`}
            >
                {isCollapsed ? 'Show full intermediate steps' : 'Hide intermediate steps'}
            </button>
            {isCollapsed && intermediateSteps.length > 0 && (
                <div className={`mt-2 p-2 text-sm text-[${colors.primary}]/70 bg-white rounded-sm break-words`}>
                    <div className="prose max-w-none prose-sm italic">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {getIntermediatePreview()}
                        </ReactMarkdown>
                    </div>
                </div>
            )}
            {!isCollapsed && intermediateSteps.length > 0 && (
                <div className={`mt-2 p-2 text-[${colors.primary}] bg-white rounded-sm`}>
                    {intermediateSteps.map((step, index) => (
                        <PerplexityIntermediateStep 
                            key={`${index}-${step.length}`} // Key changes as step content updates
                            text={step} 
                            index={index} 
                            agentId={agentId}
                            agentUuid={agentUuid}
                            isLastStep={isIntermediate && index === intermediateSteps.length - 1} // Flag for styling in-progress step
                            sessionId={sessionId}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}; 