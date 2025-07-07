import { ChatMessage as ChatMessageType } from '../types';
import { colors } from '../config/colors';
import { useEffect, useRef, useState } from 'react';
import { ReasoningDisplay } from './IntermediateDisplay';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Citations } from './Citations';
import { Citation } from '../types';

interface DeepResearchChatMessageProps {
    message: ChatMessageType;
    modelId?: 'modelA' | 'modelB';
    modelUuid?: string;
    sessionId?: string;
}

export const DeepResearchChatMessage = ({ message, modelId, modelUuid, sessionId }: DeepResearchChatMessageProps) => {
    const isUser = message.role === 'user';
    const bgColor = isUser ? colors.secondary : colors.light;
    const messageRef = useRef<HTMLDivElement>(null);
    
    // Track the message content for animation effects
    const [displayText, setDisplayText] = useState<string>(message.content[0]?.text || '');
    const [markdownText, setMarkdownText] = useState<string>('');
    const [highlightRects, setHighlightRects] = useState<Array<{top: number, left: number, width: number, height: number}> | null>(null);
    const [selectedText, setSelectedText] = useState<string>('');
    const [uniqueCitations, setUniqueCitations] = useState<Citation[]>([]);

    // Update the display text when the message content changes
    useEffect(() => {
        const newText = message.content[0]?.text || '';
        setDisplayText(newText);
        
        // Process citations in the text
        if (!isUser && newText) {
            let processedText = newText.replace(/%\[(\d+)\]%/g, '[$1]');
            
            if (message.citations) {
                const citationMap = new Map<number, number>();
                const uCitations: Citation[] = [];
                
                message.citations.forEach((citation, originalIndex) => {
                    const existingCitationIndex = uCitations.findIndex(c => c.url === citation.url);
                    if (existingCitationIndex === -1) {
                        uCitations.push(citation);
                        citationMap.set(originalIndex + 1, uCitations.length);
                    } else {
                        citationMap.set(originalIndex + 1, existingCitationIndex + 1);
                    }
                });

                setUniqueCitations(uCitations);
                
                processedText = processedText.replace(/\[(\d+)\]/g, (match, p1) => {
                    const originalCitationNumber = parseInt(p1, 10);
                    const newCitationNumber = citationMap.get(originalCitationNumber);
                    if (newCitationNumber) {
                        return `[${newCitationNumber}]`;
                    }
                    return match;
                });
            } else {
                setUniqueCitations([]);
            }

            setMarkdownText(processedText);
        } else {
            setMarkdownText(newText);
        }
    }, [message.content, message.citations, isUser]);

    // Scroll to the bottom of the message when it updates
    useEffect(() => {
        if (messageRef.current) {
            messageRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }, [markdownText]);

    useEffect(() => {
        if (!isUser && message.citations) {
            console.log('Citations received:', message.citations);
        }
    }, [isUser, message.citations]);

    const handleSpanVote = async (vote: 'up' | 'down') => {
        console.log('clicked');
        if (!selectedText) {
            console.error("No text selected for voting.");
            return;
        }

        if (!modelUuid) {
            console.error("Model UUID is missing, cannot submit vote.");
            return;
        }

        if (!sessionId) {
            console.error("Session ID is missing, cannot submit vote.");
            return;
        }

        const payload = {
            vote,
            highlighted_text: selectedText,
            model_uuid: modelUuid,
            session_id: sessionId,
        };

        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/answer-span-vote`, {
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
                console.log(`Vote (${vote}) submitted successfully for: "${selectedText}"`);
            }
        } catch (error) {
            console.error('Failed to submit vote:', error);
        }

        // Reset highlighting after vote
        setHighlightRects(null);
        setSelectedText('');
    };

    // --- Highlighting logic ---
    const handleMouseUp = () => {
        if (isUser) return;
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed || !messageRef.current) {
            setHighlightRects(null);
            setSelectedText('');
            return;
        }

        const selectedString = selection.toString().trim();
        if (!selectedString) {
            // If the selection is empty, clear the highlight
            setHighlightRects(null);
            setSelectedText('');
            return;
        }

        const range = selection.getRangeAt(0);
        // Ensure the selection is within the current message bubble
        if (!messageRef.current.contains(range.commonAncestorContainer)) {
            setHighlightRects(null);
            setSelectedText('');
            return;
        }

        const clientRects = range.getClientRects();
        const containerRect = messageRef.current.getBoundingClientRect();

        const relativeRects = Array.from(clientRects).map(rect => ({
            top: rect.top - containerRect.top,
            left: rect.left - containerRect.left,
            width: rect.width,
            height: rect.height,
        }));

        if (relativeRects.length > 0) {
            setHighlightRects(relativeRects);
            setSelectedText(selectedString);
        } else {
            setHighlightRects(null);
            setSelectedText('');
        }
        
        // Deselect the text
        selection.removeAllRanges();
    };

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
            <div 
                ref={messageRef}
                className={`max-w-[80%] rounded-lg p-4 ${isUser ? 'rounded-tr-none' : 'rounded-tl-none'}`}
                style={{ 
                    backgroundColor: bgColor,
                    minHeight: isUser ? 'auto' : '20px', // Give assistant messages a min-height so they're visible even when empty
                    position: 'relative',
                }}
            >
                {/* Display reasoning steps if available and not user message */}
                {!isUser && message.reasoning && modelId && (
                    <ReasoningDisplay 
                        reasoningText={message.reasoning} 
                        modelId={modelId} 
                        modelUuid={modelUuid}
                        isReasoning={message.isReasoning}
                        sessionId={sessionId}
                    />
                )}
                
                {/* Display final answer content */}
                <div 
                    className={`text-base ${isUser ? 'text-white' : 'text-gray-800'}`}
                >
                    <div 
                        className={`prose max-w-none ${isUser ? 'prose-invert' : ''}`}
                        onMouseUp={handleMouseUp}
                    >
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeRaw]}
                            components={{
                                a: ({node, children, ...props}) => {
                                    if (!props.href || props.href.startsWith('#')) {
                                        return <a {...props}>{children}</a>;
                                    }
                                    return <a {...props} target="_blank" rel="noopener noreferrer">{children}</a>;
                                },
                            }}
                        >
                            {markdownText}
                        </ReactMarkdown>
                    </div>
                    {!isUser && uniqueCitations.length > 0 && message.isComplete && (
                        <Citations citations={uniqueCitations} />
                    )}
                </div>

                {/* Highlight and thumbs up/down */}
                {highlightRects && highlightRects.length > 0 && (
                    <>
                        {highlightRects.map((rect, i) => (
                            <div
                                key={i}
                                style={{
                                    position: 'absolute',
                                    top: `${rect.top}px`,
                                    left: `${rect.left}px`,
                                    width: `${rect.width}px`,
                                    height: `${rect.height}px`,
                                    backgroundColor: 'rgba(187, 247, 208, 0.5)',
                                    borderRadius: '3px',
                                    pointerEvents: 'none',
                                }}
                            />
                        ))}
                        <div
                            style={{
                                position: 'absolute',
                                top: `${highlightRects[0].top}px`,
                                left: `${highlightRects[0].left + highlightRects[0].width / 2}px`,
                                transform: 'translate(-50%, -110%)',
                                display: 'flex',
                                gap: '0.25rem',
                                zIndex: 10,
                                backgroundColor: 'white',
                                padding: '2px',
                                borderRadius: '5px',
                                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                            }}
                        >
                            <button
                                onClick={() => handleSpanVote('up')}
                                className="p-1 hover:bg-gray-200 rounded"
                                title="Thumbs Up"
                            >
                                <img src="/thumbs-up-regular.svg" alt="Thumbs Up" className="h-5 w-5" />
                            </button>
                            <button
                                onClick={() => handleSpanVote('down')}
                                className="p-1 hover:bg-gray-200 rounded"
                                title="Thumbs Down"
                            >
                                <img src="/thumbs-down-regular.svg" alt="Thumbs Down" className="h-5 w-5" />
                            </button>
                        </div>
                    </>
                )}

                {!isUser && displayText === '' && !message.reasoning && (
                    <div className="flex space-x-2 mt-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '400ms' }}></div>
                    </div>
                )}
            </div>
        </div>
    );
}; 