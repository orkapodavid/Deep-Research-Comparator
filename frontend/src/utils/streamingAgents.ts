export interface Citation {
    text?: string;
    url: string;
}

export interface AgentOutput {
    content: string; // Will hold final answer
    passages: any[];
    intermediate?: string; // Will hold thinking process
    citations?: Citation[];
}

export interface StreamingResponseAgents {
    agentA: AgentOutput;
    agentB: AgentOutput;
    agentC: AgentOutput;
    metadata?: {
        passages_a: any[];
        passages_b: any[];
        passages_c: any[];
        all_agents?: any;
        agentA_type?: string;
        agentB_type?: string;
        agentC_type?: string;
    };
    is_final?: boolean;
    agentA_intermediate_steps?: string;
    agentA_final_report?: string;
    agentA_is_complete?: boolean;
    agentA_citations?: Citation[];
    agentB_intermediate_steps?: string;
    agentB_final_report?: string;
    agentB_is_complete?: boolean;
    agentB_citations?: Citation[];
    agentC_intermediate_steps?: string;
    agentC_final_report?: string;
    agentC_is_complete?: boolean;
    agentC_citations?: Citation[];
    agentA_updated?: boolean;
    agentB_updated?: boolean;
    agentC_updated?: boolean;
    agentA_is_intermediate?: boolean;
    agentB_is_intermediate?: boolean;
    agentC_is_intermediate?: boolean;
    heartbeat?: boolean;
    message?: string;
    test_message?: string;
}

export const streamAgentsResponse = async (
    url: string,
    body: any,
    onChunk: (chunk: StreamingResponseAgents) => void,
    authHeaders?: Record<string, string>
): Promise<void> => {
    console.log('Starting agents stream response to:', url);
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders,
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        // Emit a special error chunk to the UI
        onChunk({
            agentA: { content: '', passages: [], intermediate: '', citations: [] },
            agentB: { content: '', passages: [], intermediate: '', citations: [] },
            agentC: { content: '', passages: [], intermediate: '', citations: [] },
            message: `Error: Unable to connect to backend (status: ${response.status})`,
            is_final: true
        });
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error('No reader available');
    }

    let buffer = '';
    let agentAContent = '';
    let agentBContent = '';
    let agentCContent = '';
    let agentAIntermediate = '';
    let agentBIntermediate = '';
    let agentCIntermediate = '';
    let passages_a: any[] = [];
    let passages_b: any[] = [];
    let passages_c: any[] = [];
    let agentACitations: Citation[] = [];
    let agentBCitations: Citation[] = [];
    let agentCCitations: Citation[] = [];
    let all_agents: any | undefined;
    let agentA_type: string | undefined;
    let agentB_type: string | undefined;
    let agentC_type: string | undefined;
    let rawResponse = '';

    console.log('Starting to read agents stream');

    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            console.log('Agents stream complete');
            console.log('Full raw response:', rawResponse);
            break;
        }

        const chunk = new TextDecoder().decode(value);
        rawResponse += chunk;
        buffer += chunk;

        const lines = buffer.split('\n');
        
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (line.trim() === '') {
                continue;
            }
            
            try {
                const update = JSON.parse(line);

                if (update.error) {
                    // Emit error message to the UI
                    onChunk({
                        agentA: { content: '', passages: [], intermediate: '', citations: [] },
                        agentB: { content: '', passages: [], intermediate: '', citations: [] },
                        agentC: { content: '', passages: [], intermediate: '', citations: [] },
                        message: `Error: ${update.error}`,
                        is_final: true
                    });
                    continue;
                }
                
                if (update.heartbeat) {
                    console.log('Received heartbeat at:', update.timestamp);
                    continue; // Skip processing as a data chunk, just keep connection alive
                }
                
                // Debug logging for metadata and agent types
                if (update.metadata) {
                    console.log('Received metadata:', update.metadata);
                    passages_a = update.metadata.passages_a ?? passages_a;
                    passages_b = update.metadata.passages_b ?? passages_b;
                    passages_c = update.metadata.passages_c ?? passages_c;
                    all_agents = update.metadata.all_agents ?? all_agents;
                    agentA_type = update.metadata.agentA_type ?? agentA_type;
                    agentB_type = update.metadata.agentB_type ?? agentB_type;
                    agentC_type = update.metadata.agentC_type ?? agentC_type;
                }

                // Handle Agent intermediate steps updates
                if (update.agentA_intermediate_steps != null) {
                    agentAIntermediate = update.agentA_intermediate_steps;
                }
                if (update.agentB_intermediate_steps != null) {
                    agentBIntermediate = update.agentB_intermediate_steps;
                }
                if (update.agentC_intermediate_steps != null) {
                    agentCIntermediate = update.agentC_intermediate_steps;
                }

                // Update final content if provided
                if (update.agentA_final_report != null) {
                    agentAContent = update.agentA_final_report.replace(/^```markdown\n/, '').replace(/\n```$/, '');
                }
                if (update.agentB_final_report != null) {
                    agentBContent = update.agentB_final_report.replace(/^```markdown\n/, '').replace(/\n```$/, '');
                }
                if (update.agentC_final_report != null) {
                    agentCContent = update.agentC_final_report.replace(/^```markdown\n/, '').replace(/\n```$/, '');
                }

                if (update.agentA_citations && Array.isArray(update.agentA_citations)) {
                    console.log('Received raw citations for Agent A:', update.agentA_citations);
                    agentACitations = update.agentA_citations.map((url: string) => ({ url }));
                    console.log('Processed citations for Agent A:', agentACitations);
                }
                if (update.agentB_citations && Array.isArray(update.agentB_citations)) {
                    console.log('Received raw citations for Agent B:', update.agentB_citations);
                    agentBCitations = update.agentB_citations.map((url: string) => ({ url }));
                    console.log('Processed citations for Agent B:', agentBCitations);
                }
                if (update.agentC_citations && Array.isArray(update.agentC_citations)) {
                    console.log('Received raw citations for Agent C:', update.agentC_citations);
                    agentCCitations = update.agentC_citations.map((url: string) => ({ url }));
                    console.log('Processed citations for Agent C:', agentCCitations);
                }

                // Emit updated state
                const chunkToEmit: StreamingResponseAgents = {
                    agentA: {
                        content: agentAContent,
                        passages: passages_a,
                        intermediate: agentAIntermediate,
                        citations: agentACitations,
                    },
                    agentB: {
                        content: agentBContent,
                        passages: passages_b,
                        intermediate: agentBIntermediate,
                        citations: agentBCitations,
                    },
                    agentC: {
                        content: agentCContent,
                        passages: passages_c,
                        intermediate: agentCIntermediate,
                        citations: agentCCitations,
                    },
                    metadata: {
                        passages_a,
                        passages_b,
                        passages_c,
                        all_agents,
                        agentA_type,
                        agentB_type,
                        agentC_type,
                    },
                    is_final: !!update.final,
                    agentA_intermediate_steps: update.agentA_intermediate_steps,
                    agentA_final_report: update.agentA_final_report,
                    agentA_is_complete: !!update.agentA_is_complete,
                    agentA_citations: agentACitations,
                    agentB_intermediate_steps: update.agentB_intermediate_steps,
                    agentB_final_report: update.agentB_final_report,
                    agentB_is_complete: !!update.agentB_is_complete,
                    agentB_citations: agentBCitations,
                    agentC_intermediate_steps: update.agentC_intermediate_steps,
                    agentC_final_report: update.agentC_final_report,
                    agentC_is_complete: !!update.agentC_is_complete,
                    agentC_citations: agentCCitations,
                    agentA_updated: !!update.agentA_updated,
                    agentB_updated: !!update.agentB_updated,
                    agentC_updated: !!update.agentC_updated,
                    agentA_is_intermediate: !!update.agentA_is_intermediate,
                    agentB_is_intermediate: !!update.agentB_is_intermediate,
                    agentC_is_intermediate: !!update.agentC_is_intermediate
                };

                onChunk(chunkToEmit);

            } catch (e) {
                console.error('Error parsing JSON:', e);
                console.error('Problematic line:', line);
            }
        }
    }
};