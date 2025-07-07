export interface Citation {
    text?: string;
    url: string;
}

export interface ModelOutput {
    content: string; // Will hold final answer
    passages: any[];
    reasoning?: string; // Will hold thinking process
    citations?: Citation[];
}

export interface StreamingResponse {
    modelA: ModelOutput;
    modelB: ModelOutput;
    metadata?: {
        passages_a: any[];
        passages_b: any[];
        selected_models?: any;
        modelA_type?: string;
        modelB_type?: string;
    };
    final?: boolean;
    modelA_think?: string;
    modelA_final?: string;
    modelA_complete?: boolean;
    modelA_citations?: Citation[];
    modelB_think?: string;
    modelB_final?: string;
    modelB_complete?: boolean;
    modelB_citations?: Citation[];
    modelA_updated?: boolean;
    modelB_updated?: boolean;
    modelA_isReasoning?: boolean;
    modelB_isReasoning?: boolean;
    heartbeat?: boolean;
    message?: string;
    test_message?: string;
}

export const streamResponse = async (
    url: string,
    body: any,
    onChunk: (chunk: StreamingResponse) => void
): Promise<void> => {
    console.log('Starting stream response to:', url);
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error('No reader available');
    }

    let buffer = '';
    let modelAContent = '';
    let modelBContent = '';
    let modelAReasoning = '';
    let modelBReasoning = '';
    let passages_a: any[] = [];
    let passages_b: any[] = [];
    let modelACitations: Citation[] = [];
    let modelBCitations: Citation[] = [];
    let selected_models: any | undefined;
    let modelA_type: string | undefined;
    let modelB_type: string | undefined;
    let rawResponse = '';

    console.log('Starting to read stream');

    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            console.log('Stream complete');
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

                if (update.heartbeat) {
                    console.log('Received heartbeat at:', update.timestamp);
                    continue; // Skip processing as a data chunk, just keep connection alive
                }
                
                // Debug logging for metadata and model types
                if (update.metadata) {
                    console.log('Received metadata:', update.metadata);
                    passages_a = update.metadata.passages_a ?? passages_a;
                    passages_b = update.metadata.passages_b ?? passages_b;
                    selected_models = update.metadata.selected_models ?? selected_models;
                    modelA_type = update.metadata.modelA_type ?? modelA_type;
                    modelB_type = update.metadata.modelB_type ?? modelB_type;
                }

                // Handle Model A thinking updates by replacing the content
                if (update.modelA_think != null) {
                    modelAReasoning = update.modelA_think;
                }

                // Handle Model B thinking updates by replacing the content
                if (update.modelB_think != null) {
                    modelBReasoning = update.modelB_think;
                }

                // Update final content if provided
                if (update.modelA_final != null) {
                    modelAContent = update.modelA_final.replace(/^```markdown\n/, '').replace(/\n```$/, '');
                }
                if (update.modelB_final != null) {
                    modelBContent = update.modelB_final.replace(/^```markdown\n/, '').replace(/\n```$/, '');
                }

                if (update.modelA_citations && Array.isArray(update.modelA_citations)) {
                    console.log('Received raw citations for Model A:', update.modelA_citations);
                    modelACitations = update.modelA_citations.map((url: string) => ({ url }));
                    console.log('Processed citations for Model A:', modelACitations);
                }
                if (update.modelB_citations && Array.isArray(update.modelB_citations)) {
                    console.log('Received raw citations for Model B:', update.modelB_citations);
                    modelBCitations = update.modelB_citations.map((url: string) => ({ url }));
                    console.log('Processed citations for Model B:', modelBCitations);
                }

                // Emit updated state
                const chunkToEmit: StreamingResponse = {
                    modelA: {
                        content: modelAContent,
                        passages: passages_a,
                        reasoning: modelAReasoning,
                        citations: modelACitations,
                    },
                    modelB: {
                        content: modelBContent,
                        passages: passages_b,
                        reasoning: modelBReasoning,
                        citations: modelBCitations,
                    },
                    metadata: {
                        passages_a,
                        passages_b,
                        selected_models,
                        modelA_type,
                        modelB_type,
                    },
                    final: !!update.final,
                    modelA_think: update.modelA_think,
                    modelA_final: update.modelA_final,
                    modelA_complete: !!update.modelA_complete,
                    modelA_citations: modelACitations,
                    modelB_think: update.modelB_think,
                    modelB_final: update.modelB_final,
                    modelB_complete: !!update.modelB_complete,
                    modelB_citations: modelBCitations,
                    modelA_updated: !!update.modelA_updated,
                    modelB_updated: !!update.modelB_updated,
                    modelA_isReasoning: !!update.modelA_isReasoning,
                    modelB_isReasoning: !!update.modelB_isReasoning
                };

                onChunk(chunkToEmit);

            } catch (e) {
                console.error('Error parsing JSON:', e);
                console.error('Problematic line:', line);
            }
        }
    }
}; 