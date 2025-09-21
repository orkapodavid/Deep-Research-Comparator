export interface AgentOutput {
    content: string;
    passages: any[];
    intermediate?: string;
}

export interface StreamingResponse {
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

export interface AgentOutputs {
    agentA: AgentOutput;
    agentB: AgentOutput;
    agentC: AgentOutput;
}

export interface ConversationTurn {
    question: string;
    answer: string;
}

export interface ConversationHistory {
    agentA: ConversationTurn[];
    agentB: ConversationTurn[];
    agentC: ConversationTurn[];
}

export interface AgentDetails {
    AgentA: string;
    AgentB: string;
    AgentC: string;
}

export interface SessionData {
    sessionId?: string | null;
    currentQuestion: string;
    selectedChoice: string;
    selectedAgents?: any[];
    selectedTeams?: any[];
}

export type ChoiceType = 'choice1' | 'choice2' | 'choice3' | 'choice4';

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
    intermediate_steps?: string;
    citations?: Citation[];
    is_intermediate?: boolean;
    is_complete?: boolean;
}

export interface ChatHistory {
    messages: ChatMessage[];
}

export interface AgentInfo {
    id: string;
    agent_id: string;
    name: string;
} 