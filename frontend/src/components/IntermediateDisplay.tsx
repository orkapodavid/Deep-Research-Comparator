import { useState } from 'react';
import { colors } from '../config/colors';
import { PerplexityReasoningStep } from './IntermediateStep';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ReasoningDisplayProps {
    reasoningText: string;
    modelId: 'modelA' | 'modelB';
    isReasoning?: boolean;
    modelUuid?: string;
    sessionId?: string;
}

export const ReasoningDisplay = ({ reasoningText, modelId, isReasoning = false, modelUuid, sessionId }: ReasoningDisplayProps) => {
    const [isCollapsed, setIsCollapsed] = useState(true);

    if (!reasoningText) {
        console.log('No reasoning text provided');
        return null;
    }
    console.log('modelUuid', modelUuid);

    let reasoningSteps: string[] = [];
    
    if (modelUuid === "888e417d-0993-4101-a9e6-a49b308e2ccc" || modelUuid === "56098a16-58d3-46e1-91ed-15e7feefc98d") {
        // For perplexity and gpt-researcher models, split by double newlines
        const normalizedText = reasoningText.replace(/\\n/g, '\n').trim();
        console.log('normalizedText', normalizedText);
        
        // Split by double newlines to get all steps (including in-progress)
        reasoningSteps = normalizedText
            .split('\n\n')
            .map(step => step.trim())
            .filter(step => step !== '');
            
    } else {
        // For baseline model, the reasoning text is a markdown-like string.
        // Steps are separated by "### Step <number>".
        const normalizedText = reasoningText.replace(/\\n/g, '\n').trim();
        if (normalizedText) {
            const stepRegex = /### Step \d+[\s\S]*?(?=(?:### Step \d+|$))/g;
            const matches = normalizedText.match(stepRegex);
            if (matches && matches.length > 0) {
                reasoningSteps = matches.map(step => step.trim());
            } else {
                // If no steps are found but text exists, show it as a single block.
                // This could happen if the reasoning text is just one chunk without the '### Step' header.
                reasoningSteps = [normalizedText];
            }
        }
    }
    console.log('reasoningSteps:', reasoningSteps);

    const getReasoningPreview = () => {
        if (reasoningSteps.length === 0) {
            return "";
        }

        const lastThreeSteps = reasoningSteps.slice(-3);
        const previewText = lastThreeSteps.map(step => {
            if (modelUuid !== "888e417d-0993-4101-a9e6-a49b308e2ccc" && modelUuid !== "56098a16-58d3-46e1-91ed-15e7feefc98d") {
                return step.replace(/### Step \d+[:\s]*/, '').trim();
            }
            return step;
        }).join('\n');
        
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
            {isCollapsed && reasoningSteps.length > 0 && (
                <div className={`mt-2 p-2 text-sm text-[${colors.primary}]/70 bg-white rounded-sm break-words`}>
                    <div className="prose max-w-none prose-sm italic">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {getReasoningPreview()}
                        </ReactMarkdown>
                    </div>
                </div>
            )}
            {!isCollapsed && reasoningSteps.length > 0 && (
                <div className={`mt-2 p-2 text-[${colors.primary}] bg-white rounded-sm`}>
                    {reasoningSteps.map((step, index) => (
                        <PerplexityReasoningStep 
                            key={`${index}-${step.length}`} // Key changes as step content updates
                            text={step} 
                            index={index} 
                            modelId={modelId}
                            modelUuid={modelUuid}
                            isLastStep={isReasoning && index === reasoningSteps.length - 1} // Flag for styling in-progress step
                            sessionId={sessionId}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}; 