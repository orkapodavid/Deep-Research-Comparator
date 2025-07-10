export interface AgentOutput {
    content: string;
    passages: any[];
    intermediate?: string;
}

export interface StreamingResponse {
    agentA: AgentOutput;
    agentB: AgentOutput;
    metadata?: {
        passages_a: any[];
        passages_b: any[];
        selected_agents?: any[];
        agent1_type?: 'baseline' | 'perplexity';
        agent2_type?: 'baseline' | 'perplexity';
    };
    final?: boolean;
    agent1?: string;
    agent2?: string;
    agent1_complete?: boolean;
    agent2_complete?: boolean;
    agentA_updated?: boolean;
    agentB_updated?: boolean;
    agentA_isIntermediate?: boolean;
    agentB_isIntermediate?: boolean;
    heartbeat?: boolean;
    message?: string;
    test_message?: string;
}

export interface AgentOutputs {
    agentA: AgentOutput;
    agentB: AgentOutput;
}

export interface ConversationTurn {
    question: string;
    answer: string;
}

export interface ConversationHistory {
    agentA: ConversationTurn[];
    agentB: ConversationTurn[];
}

export interface AgentDetails {
    AgentA: string;
    AgentB: string;
}

export interface SessionData {
    sessionId?: string | null;
    currentQuestion: string;
    selectedChoice: string;
    selectedAgents?: any[];
    selectedTeams?: any[];
}

export type ChoiceType = 'choice1' | 'choice2' | 'choice3' | 'choice4';

export interface RankingRow {
    rank: number;
    systemname: string;
    score: number;
    votes: number;
    stepupvote: number;
    textupvote: number;

}

export interface MessageContent {
    text: string;
}

export interface Citation {
    text?: string;
    url: string;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: MessageContent[];
    intermediate?: string;
    citations?: Citation[];
    isIntermediate?: boolean;
    isComplete?: boolean;
}

export interface ChatHistory {
    messages: ChatMessage[];
} 