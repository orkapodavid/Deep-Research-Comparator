import React, { useState } from 'react';
import { colors } from '../config/colors';

interface QuestionInputProps {
    onSubmit: (question: string) => void;
    disabled: boolean;
}

export const QuestionInput = ({ onSubmit, disabled }: QuestionInputProps) => {
    const [question, setQuestion] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (question.trim()) {
            onSubmit(question.trim());
            setQuestion('');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="mb-4">
            <div className="flex gap-4 items-end">
                <div className="flex-1">
                    <label htmlFor="question-input" className={`block text-sm font-medium text-[${colors.primary}] mb-1`}>
                        Your Question:
                    </label>
                    <input
                        type="text"
                        id="question-input"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Enter your question here..."
                        disabled={disabled}
                        className={`w-full p-2 border border-[${colors.secondary}] rounded-md focus:ring-[${colors.primary}] focus:border-[${colors.primary}]`}
                    />
                </div>
                <button
                    type="submit"
                    disabled={disabled}
                    style={{ backgroundColor: colors.secondary }} 
                    className={`px-4 py-2 bg-[${colors.primary}] text-[#F9F7F7] rounded-md hover:bg-[${colors.secondary}] focus:outline-none focus:ring-2 focus:ring-[${colors.primary}] focus:ring-offset-2 disabled:opacity-50`}
                >
                    Submit
                </button>
            </div>
        </form>
    );
}; 