import { Citation } from '../types';
import React from 'react';
import { colors } from '../config/colors';

interface CitationsProps {
    citations: Citation[];
}

export const Citations: React.FC<CitationsProps> = ({ citations }) => {
    if (!citations || citations.length === 0) {
        return null;
    }

    return (
        <div className="mt-4 p-4 border-t border-gray-200">
            <h4 className="font-semibold text-base mb-2 text-gray-600">Citations</h4>
            <div className="flex flex-wrap gap-x-2 gap-y-1">
                {citations.map((citation, index) => (
                    <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        key={index}
                        className="text-sm hover:underline"
                        style={{ color: colors.secondary }}
                        title={citation.url}
                    >
                        {`[${index + 1}]`}
                    </a>
                ))}
            </div>
        </div>
    );
};
