import { useState } from 'react';
import { colors } from '../config/colors';
import { PerplexityIntermediateStep } from './IntermediateStep';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface IntermediateDisplayProps {
    intermediateText: string;
    agentId: 'agentA' | 'agentB';
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

    let intermediateSteps: string[] = [];
     if (agentUuid === import.meta.env.VITE_PERPLEXITY_AGENT_UUID || agentUuid === import.meta.env.VITE_GPT_RESEARCHER_AGENT_UUID) {
        // For perplexity and gpt-researcher agents, split by double newlines
        const normalizedText = intermediateText.replace(/\\n/g, '\n').trim();
        console.log('inside this if statement');
        console.log('normalizedText', normalizedText);
        
        // Split by double newlines to get all steps (including in-progress)
        intermediateSteps = normalizedText
            .split('\n\n')
            .map(step => step.trim())
            .filter(step => step !== '');
            
    } else {
        // For baseline agent, the intermediate text is a markdown-like string.
        // Steps are separated by "### Step <number>".
        const normalizedText = intermediateText.replace(/\\n/g, '\n').trim();
        if (normalizedText) {
            const stepRegex = /### Step \d+[\s\S]*?(?=(?:### Step \d+|$))/g;
            const matches = normalizedText.match(stepRegex);
            if (matches && matches.length > 0) {
                intermediateSteps = matches.map(step => step.trim());
            } else {
                // If no steps are found but text exists, show it as a single block.
                // This could happen if the intermediate text is just one chunk without the '### Step' header.
                intermediateSteps = [normalizedText];
            }
        }
    }
    console.log('intermediateSteps:', intermediateSteps);

    const getIntermediatePreview = () => {
        if (intermediateSteps.length === 0) {
            return "";
        }

        const lastThreeSteps = intermediateSteps.slice(-3);
        const previewText = lastThreeSteps.map(step => {
            if (agentUuid !== "888e417d-0993-4101-a9e6-a49b308e2ccc" && agentUuid !== "56098a16-58d3-46e1-91ed-15e7feefc98d") {
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