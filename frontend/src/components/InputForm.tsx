import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Brain, SendHorizontal, StopCircle, Sparkles, Search } from "lucide-react"; // Added Search
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils"; // For conditional classes

interface InputFormProps {
  onSubmit: (inputValue: string) => void;
  onCancel: () => void;
  isLoading: boolean;
  hasHistory: boolean; // To show "New Search" button
  researchMode: string;
  onResearchModeChange: (mode: string) => void;
}

export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  onCancel,
  isLoading,
  hasHistory,
  researchMode,
  onResearchModeChange,
}) => {
  const [internalInputValue, setInternalInputValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleInternalSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!internalInputValue.trim() || isLoading) return;
    onSubmit(internalInputValue);
    // Do not clear input here, App.tsx will manage clearing on new message stream
  };

  const handleInternalKeyDown = (
    e: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (e.key === "Enter" && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleInternalSubmit();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"; // Reset height
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`; // Max height 200px
    }
  }, [internalInputValue]);

  // Focus textarea on initial load
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);


  const isSubmitDisabled = !internalInputValue.trim() || isLoading;

  return (
    <form
      onSubmit={handleInternalSubmit}
      className="flex flex-col gap-3 p-1 w-full" // Reduced gap slightly
    >
      <div className="relative w-full">
        {/* Gradient border effect - visible when textarea is focused or input has value */}
        <div
          className={cn(
            "absolute -inset-0.5 rounded-3xl bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 opacity-0 transition-opacity duration-300 ease-in-out blur",
            (internalInputValue || textareaRef.current === document.activeElement) && !isLoading ? "opacity-50 group-hover:opacity-75" : "",
            isLoading ? "opacity-20" : "" // Dimmer when loading
          )}
        />
        <Textarea
          ref={textareaRef}
          value={internalInputValue}
          onChange={(e) => setInternalInputValue(e.target.value)}
          onKeyDown={handleInternalKeyDown}
          placeholder="What are you curious about?"
          className={cn(
            "relative w-full text-neutral-100 placeholder-neutral-400 resize-none border-none focus:outline-none focus:ring-0",
            "outline-none focus-visible:ring-0 shadow-none bg-neutral-800/80 backdrop-blur-sm",
            "md:text-base min-h-[58px] max-h-[200px] rounded-3xl py-4 pl-5 pr-16", // Increased padding
            "transition-all duration-300 ease-in-out group" // For group hover effect on gradient
          )}
          rows={1}
          disabled={isLoading}
        />
        <div className="absolute top-1/2 right-3 transform -translate-y-1/2 flex items-center">
          {isLoading ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-red-500 hover:text-red-400 hover:bg-red-900/50 p-2 rounded-full transition-all duration-200"
              onClick={onCancel}
              aria-label="Stop generation"
            >
              <StopCircle className="h-5 w-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              variant="ghost"
              size="icon"
              className={cn(
                "p-2 rounded-full transition-all duration-200",
                isSubmitDisabled
                  ? "text-neutral-600"
                  : "text-orange-500 hover:text-orange-400 hover:bg-orange-900/50"
              )}
              disabled={isSubmitDisabled}
              aria-label="Send message"
            >
              <SendHorizontal className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-neutral-400 px-2">
        <div className="flex items-center gap-2 group">
          <Brain className="h-4 w-4 text-purple-400 group-hover:text-purple-300 transition-colors" />
          <span className="mr-1 group-hover:text-neutral-300 transition-colors">Research:</span>
          <Select value={researchMode} onValueChange={onResearchModeChange} disabled={isLoading}>
            <SelectTrigger
              className="w-auto bg-transparent border-none focus:ring-0 p-0 h-auto hover:text-neutral-200 transition-colors"
              aria-label="Select research mode"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-neutral-800 border-neutral-700 text-neutral-300 shadow-xl">
              <SelectItem value="Normal" className="cursor-pointer hover:bg-neutral-700 focus:bg-neutral-700">
                Normal
              </SelectItem>
              <SelectItem value="Deep Research" className="cursor-pointer hover:bg-neutral-700 focus:bg-neutral-700">
                Deep Research
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {hasHistory && (
          <Button
            variant="ghost"
            size="sm"
            className="text-neutral-400 hover:text-neutral-200 hover:bg-neutral-700/50 px-2 py-1 h-auto"
            onClick={() => window.location.reload()} // Or a more sophisticated state reset
            disabled={isLoading}
            aria-label="Start new search"
          >
            <Search className="h-3.5 w-3.5 mr-1.5" />
            New Search
          </Button>
        )}
      </div>
    </form>
  );
};
