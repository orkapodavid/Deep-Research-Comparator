import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAuth } from '../contexts/AuthContext';

interface IntermediateStepProps {
  text: string;
  index: number;
  agentId: 'agentA' | 'agentB' | 'agentC';
  isLastStep?: boolean;
  agentUuid?: string;
  sessionId?: string;
}

export const PerplexityIntermediateStep: React.FC<IntermediateStepProps> = ({ text, index, agentId, isLastStep = false, agentUuid, sessionId }) => {
  const { getAuthHeaders } = useAuth();
  const [isHovered, setIsHovered] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);

  const handleVote = async (vote: 'up' | 'down') => {
    if (hasVoted) return; // Prevent multiple votes

    if (!agentUuid) {
        console.error('Agent UUID not provided for voting on intermediate step.');
        return;
    }

    if (!sessionId) {
      console.error('Session ID not provided for voting on intermediate step.');
      return;
    }

    const payload = {
        vote,
        step_text: text,
        agent_uuid: agentUuid,
        session_id: sessionId,
    };

    try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/intermediate-step-vote`, {
            method: 'POST',
            headers: getAuthHeaders(),
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
      key={`intermediate-step-${index}-${agentId}`}
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