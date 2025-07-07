import { useState, useEffect } from 'react';
import { LeaderboardRow } from '../types';
import { colors } from '../config/colors';

export const Leaderboard = () => {
    const [leaderboardData, setLeaderboardData] = useState<LeaderboardRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchLeaderboardData = async () => {
            try {
                const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/leaderboard`);
                if (!response.ok) {
                    throw new Error('Failed to fetch leaderboard data');
                }
                const data = await response.json();
                
                if (data.status === 'success' && Array.isArray(data.leaderboard)) {
                    setLeaderboardData(data.leaderboard);
                } else {
                    throw new Error('Invalid leaderboard data format');
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
                console.error('Leaderboard error:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchLeaderboardData();
    }, []);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className={`animate-spin rounded-full h-12 w-12 border-b-2 border-${colors.primary}`}></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center p-4 text-red-500">
                Error: {error}
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto p-4">
            <h1 className="text-3xl font-bold mb-6 text-[#112D4E]">Agent Rankings</h1>
            
            <div className="overflow-x-auto shadow-lg rounded-lg">
                <table className="min-w-full border border-[#DBE2EF] rounded-lg">
                    <thead className="bg-[#112D4E]">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-[#F9F7F7] uppercase tracking-wider">
                                Rank
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-[#F9F7F7] uppercase tracking-wider">
                                Deepresearch System
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-[#F9F7F7] uppercase tracking-wider">
                                Arena Score
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-[#F9F7F7] uppercase tracking-wider">
                                Votes
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-[#F9F7F7] uppercase tracking-wider">
                                Step UpVote Rate
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-[#F9F7F7] uppercase tracking-wider">
                                Text Upvote Rate
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#DBE2EF] bg-[#F9F7F7]">
                        {leaderboardData.map((row, index) => (
                            <tr 
                                key={`${row.systemname}-${row.rank}`} 
                                className={`hover:bg-[#DBE2EF] transition-colors ${index < 3 ? 'bg-opacity-90' : ''}`}
                            >
                                <td className="px-4 py-3 whitespace-nowrap">
                                    <span className={`inline-flex items-center justify-center ${index === 0 ? 'bg-yellow-100 text-yellow-800' : index === 1 ? 'bg-gray-100 text-gray-800' : index === 2 ? 'bg-amber-100 text-amber-800' : ''} ${index < 3 ? 'w-7 h-7 rounded-full font-bold' : ''}`}>
                                        {row.rank}
                                    </span>
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[#3F72AF]">
                                    {row.systemname}
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm text-[#112D4E]">
                                    {row.score}
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm text-[#112D4E]">
                                    {row.votes}
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold text-[#112D4E]">
                                    {row.stepupvote}
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold text-[#112D4E]">
                                    {row.textupvote}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}; 