import React, { useState, useEffect, useRef } from "react";
import { InputForm } from "./InputForm";
import CustomTextEffect from "./CustomTextEffect"; // Assuming this is in the same directory

interface WelcomeScreenProps {
  handleSubmit: (submittedInputValue: string) => void;
  onCancel: () => void;
  isLoading: boolean;
  researchMode: string;
  onResearchModeChange: (mode: string) => void;
  hasHistory: boolean;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  handleSubmit,
  onCancel,
  isLoading,
  researchMode,
  onResearchModeChange,
  hasHistory,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const novahTitleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (novahTitleRef.current) {
        const rect = novahTitleRef.current.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        novahTitleRef.current.style.setProperty("--mouse-x", `${x}px`);
        novahTitleRef.current.style.setProperty("--mouse-y", `${y}px`);
      }
    };

    const currentRef = novahTitleRef.current;
    if (currentRef) {
      currentRef.addEventListener("mousemove", handleMouseMove);
    }

    // Set focus to the Novah title initially for the glow effect
    setIsFocused(true);

    return () => {
      if (currentRef) {
        currentRef.removeEventListener("mousemove", handleMouseMove);
      }
    };
  }, []);

  return (
    <div className="flex flex-col items-center justify-center text-center px-4 flex-1 w-full max-w-3xl mx-auto animate-fadeInUp">
      <div
        className="mb-10 relative" // Increased bottom margin
        onMouseEnter={() => setIsFocused(true)}
        onMouseLeave={() => setIsFocused(false)}
        tabIndex={-1} // Make it focusable
        ref={novahTitleRef}
      >
        <CustomTextEffect
          text="Novah"
          baseClass={`novah-title text-7xl md:text-8xl font-bold ${isFocused ? 'focused' : ''}`}
          charClass="novah-char"
          animationDelay={100}
          animationDuration="0.8s"
          finalClass="tracking-tight" // Example final class for tighter tracking after animation
        />
        <CustomTextEffect
          text="Your Advanced AI Agent"
          baseClass="text-xl md:text-2xl text-neutral-400 mt-2 animate-fadeInUp animation-delay-700"
          charClass="inline-block animate-fadeInUp"
          animationDelay={30} // Faster per char
          animationDuration="0.5s" // Faster animation
        />
      </div>
      <div className="w-full p-1.5 rounded-xl shadow-2xl bg-neutral-800/60 backdrop-blur-md border border-neutral-700/80">
        <InputForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          onCancel={onCancel}
          hasHistory={hasHistory}
          researchMode={researchMode}
          onResearchModeChange={onResearchModeChange}
        />
      </div>
      <p className="text-xs text-neutral-500 mt-10 animate-fadeInUp animation-delay-1500">
        Powered by Google Gemini & LangGraph.
      </p>
    </div>
  );
};
