import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ReasoningStepProps {
  text: string;
  index: number;
  modelId: 'modelA' | 'modelB';
  isLastStep?: boolean;
  modelUuid?: string;
  sessionId?: string;
}

export const PerplexityReasoningStep: React.FC<ReasoningStepProps> = ({ text, index, modelId, isLastStep = false, modelUuid, sessionId }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);

  const handleVote = async (vote: 'up' | 'down') => {
    if (hasVoted) return; // Prevent multiple votes

    if (!modelUuid) {
        console.error('Model UUID not provided for voting on reasoning step.');
        return;
    }

    if (!sessionId) {
      console.error('Session ID not provided for voting on reasoning step.');
      return;
    }

    const payload = {
        vote,
        step_text: text,
        model_uuid: modelUuid,
        session_id: sessionId,
    };

    try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/reasoning-step-vote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error submitting vote:', errorData);
        } else {
            console.log(`Vote (${vote}) submitted successfully for step ${index}: "${text}"`);
            setHasVoted(true); // Mark as voted
            setIsHovered(false); // Hide buttons after voting
        }
    } catch (error) {
        console.error('Failed to submit vote:', error);
    }
  };

  return (
    <div 
      className={`relative mb-1 text-sm p-1 rounded hover:bg-gray-100 break-words ${
        isLastStep ? 'border-l-2 border-blue-500 pl-2' : ''
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      key={`reasoning-step-${index}-${modelId}`}
    >
      <div className={isLastStep ? 'animate-typing' : ''}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
      </div>

      {isHovered && !isLastStep && !hasVoted && (
        <div 
          className="absolute top-0 right-0 flex items-center bg-white bg-opacity-90 p-1 rounded shadow-md"
          style={{ transform: 'translateY(-100%)' }}
        >
          <button 
            onClick={() => handleVote('up')}
            className="p-1 hover:bg-gray-200 rounded"
            title="Thumbs Up"
          >
            <img src="/thumbs-up-regular.svg" alt="Thumbs Up" className="h-5 w-5" />
          </button>
          <button 
            onClick={() => handleVote('down')}
            className="p-1 ml-1 hover:bg-gray-200 rounded"
            title="Thumbs Down"
          >
            <img src="/thumbs-down-regular.svg" alt="Thumbs Down" className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
}; 