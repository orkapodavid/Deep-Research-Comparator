import { colors } from '../config/colors';

interface AgentInfo {
    name: string;
    id: string;
}

interface DeepResearchAgentDetailsProps {
    details: {
        AgentA: AgentInfo | null;
        AgentB: AgentInfo | null;
    };
}

export const DeepResearchAgentDetails = ({ details }: DeepResearchAgentDetailsProps) => {
    // Only render if either AgentA or AgentB has content
    if (!details.AgentA && !details.AgentB) {
        return null;
    }

    const renderDetail = (agentInfo: AgentInfo | null) => {
        if (!agentInfo) {
            return 'No details available';
        }
        return `Agent Name: ${agentInfo.name}`;
    };

    return (
        <div className="mt-4">
            <h3 className={`text-lg font-semibold mb-2 text-[${colors.primary}]`}>
                Agent Details
            </h3>
            <div className={`overflow-x-auto border border-[${colors.secondary}] rounded-lg`}>
                <table className="min-w-full divide-y divide-[${colors.secondary}]">
                    <thead className={`bg-[${colors.primary}]`}>
                        <tr>
                            <th scope="col" className={`px-6 py-3 text-left text-xs font-medium text-[${colors.background}] uppercase tracking-wider`}>
                                Agent
                            </th>
                            <th scope="col" className={`px-6 py-3 text-left text-xs font-medium text-[${colors.background}] uppercase tracking-wider`}>
                                Details
                            </th>
                        </tr>
                    </thead>
                    <tbody className={`bg-[${colors.background}] divide-y divide-[${colors.secondary}]`}>
                        <tr>
                            <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-[${colors.primary}]`}>
                                Agent A
                            </td>
                            <td className={`px-6 py-4 text-sm text-[${colors.primary}]`}>
                                {renderDetail(details.AgentA)}
                            </td>
                        </tr>
                        <tr>
                            <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-[${colors.primary}]`}>
                                Agent B
                            </td>
                            <td className={`px-6 py-4 text-sm text-[${colors.primary}]`}>
                                {renderDetail(details.AgentB)}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}; 