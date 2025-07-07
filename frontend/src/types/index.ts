export interface ModelOutput {
    content: string;
    passages: any[];
    reasoning?: string;
}

export interface StreamingResponse {
    modelA: ModelOutput;
    modelB: ModelOutput;
    metadata?: {
        passages_a: any[];
        passages_b: any[];
        selected_models?: any[];
        model1_type?: 'baseline' | 'perplexity';
        model2_type?: 'baseline' | 'perplexity';
    };
    final?: boolean;
    model1?: string;
    model2?: string;
    model1_complete?: boolean;
    model2_complete?: boolean;
    modelA_updated?: boolean;
    modelB_updated?: boolean;
    modelA_isReasoning?: boolean;
    modelB_isReasoning?: boolean;
    heartbeat?: boolean;
    message?: string;
    test_message?: string;
}

export interface ModelOutputs {
    modelA: ModelOutput;
    modelB: ModelOutput;
}

export interface ConversationTurn {
    question: string;
    answer: string;
}

export interface ConversationHistory {
    modelA: ConversationTurn[];
    modelB: ConversationTurn[];
}

export interface ModelDetails {
    ModelA: string;
    ModelB: string;
}

export interface SessionData {
    sessionId?: string | null;
    currentQuestion: string;
    selectedChoice: string;
    selectedModels?: any[];
    selectedTeams?: any[];
}

export type ChoiceType = 'choice1' | 'choice2' | 'choice3' | 'choice4';

export interface LeaderboardRow {
    rank: number;
    systemname: string;
    stepupvote: number;
    textupvote: number;
    score: number;
    votes: number;
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
    reasoning?: string;
    citations?: Citation[];
    isReasoning?: boolean;
    isComplete?: boolean;
}

export interface ChatHistory {
    messages: ChatMessage[];
} 