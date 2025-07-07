import { ChoiceType } from '../types';
import { colors } from '../config/colors';

interface ChoiceButtonsProps {
    onChoice: (choice: ChoiceType) => void;
    disabled: boolean;
    hasAnswered: boolean;
}

export const ChoiceButtons = ({ onChoice, disabled, hasAnswered }: ChoiceButtonsProps) => {
    const choices = [
        { id: 'choice1' as ChoiceType, label: 'Agent A is Better' },
        { id: 'choice2' as ChoiceType, label: 'Agent B is Better' },
        { id: 'choice3' as ChoiceType, label: 'Tie' },
        { id: 'choice4' as ChoiceType, label: 'Both are bad' },
    ];

    return (
        <div className="mt-4">
            <h3 className={`text-lg font-medium mb-3 text-${colors.primary} text-center`}>
                Which agent provided the better response?
            </h3>
            <div className="flex gap-4">
                {choices.map((choice) => (
                    <button
                        key={choice.id}
                        id={choice.id}
                        onClick={() => onChoice(choice.id)}
                        disabled={disabled || hasAnswered}
                        style={{ backgroundColor: colors.secondary }}
                        className="px-4 py-2 text-[#F9F7F7] rounded-md hover:bg-[#213555] focus:outline-none focus:ring-2 focus:ring-[#213555] focus:ring-offset-2 disabled:opacity-50 flex-1 transition-colors duration-200"
                    >
                        {choice.label}
                    </button>
                ))}
            </div>
        </div>
    );
}; 