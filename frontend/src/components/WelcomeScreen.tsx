import { InputForm } from "./InputForm";

// Updated WelcomeScreenProps for Step 4
interface WelcomeScreenProps {
  // handleSubmit will be simplified after App.tsx's handleSubmit is updated in Step 5
  // For now, keep its signature as App.tsx expects, but we know InputForm will call it differently soon.
  // Or, more correctly, InputForm's onSubmit prop type should match what it actually calls.
  // Let's assume App.tsx's handleSubmit is already (inputValue: string, researchMode: string) from Step 2.
  // And InputForm's onSubmit is (inputValue: string) from Step 3.
  // So WelcomeScreen needs to adapt the call or App.tsx needs to provide a compatible handleSubmit.
  // The instruction says: "App.tsx`'s `handleSubmit` function (passed to `WelcomeScreen` and then to `InputForm`'s `onSubmit` prop,
  // potentially renamed) should be `(inputValue: string) => { /* ... access researchMode from App.tsx's state ... make API call ... */ }`."
  // This means WelcomeScreen will receive this simplified handleSubmit.
  handleSubmit: (submittedInputValue: string) => void; // This is what InputForm will call
  onCancel: () => void;
  isLoading: boolean;
  researchMode: string; // from App.tsx
  onResearchModeChange: (mode: string) => void; // from App.tsx
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  handleSubmit,
  onCancel,
  isLoading,
  researchMode,
  onResearchModeChange,
}) => (
  <div className="flex flex-col items-center justify-center text-center px-4 flex-1 w-full max-w-2xl mx-auto"> {/* Reduced max-width for focus */}
    <div className="mb-8"> {/* Increased bottom margin */}
      <h1 className="text-4xl md:text-5xl font-semibold text-neutral-100 mb-2"> {/* Slightly smaller h1 */}
        Research Agent
      </h1>
      <p className="text-lg md:text-xl text-neutral-400">
        What would you like to explore today?
      </p>
    </div>
    <div className="w-full p-2 rounded-xl shadow-2xl bg-neutral-800"> {/* Added a subtle background and shadow to InputForm container */}
      <InputForm
        onSubmit={handleSubmit}
        isLoading={isLoading}
        onCancel={onCancel}
        hasHistory={false}
        researchMode={researchMode}
        onResearchModeChange={onResearchModeChange}
      />
    </div>
    <p className="text-xs text-neutral-500 mt-8"> {/* Increased top margin */}
      Powered by Google Gemini & LangGraph
    </p>
  </div>
);
