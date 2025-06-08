import React, { useEffect, useRef, useState } from "react";
import { CognitiveBlockData, Source } from "@/types";
import { CognitiveBlock } from "./CognitiveBlock";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronDown, ChevronRight, Link as LinkIcon, Loader2, Brain } from "lucide-react"; // Added Loader2, Brain

interface ThoughtStreamPanelProps {
  thoughts: CognitiveBlockData[];
  isLoadingNextThought: boolean;
  currentGoal: string;
  sources: Source[];
  // Collapsible props - managed by parent (ChatLayout)
  // isCollapsed: boolean;
  // onToggle: () => void;
  // The provided code for ThoughtStreamPanel itself doesn't implement the main panel collapse,
  // but ChatLayout would handle that. This component manages its internal "Cited Sources" collapse.
}

export const ThoughtStreamPanel: React.FC<ThoughtStreamPanelProps> = ({
  thoughts,
  isLoadingNextThought,
  currentGoal,
  sources,
}) => {
  const thoughtsScrollRef = useRef<HTMLDivElement>(null);
  const sourcesScrollRef = useRef<HTMLDivElement>(null);
  const [isSourcesOpen, setIsSourcesOpen] = useState(true);

  useEffect(() => {
    if (thoughtsScrollRef.current) {
      thoughtsScrollRef.current.scrollTop = thoughtsScrollRef.current.scrollHeight;
    }
  }, [thoughts, isLoadingNextThought]); // Scroll thoughts when new thoughts or loading state changes

  return (
    <div className="thought-stream-panel bg-neutral-900/80 p-0 rounded-lg shadow-inner h-full flex flex-col text-neutral-100 border border-neutral-700/90 overflow-hidden">
      {/* Header Section: Goal */}
      <div className="px-3 pt-3 pb-2 border-b border-neutral-700/90 bg-neutral-900/90">
        <div className="flex items-center text-sm font-semibold text-neutral-200 mb-1 truncate">
          <Brain size={15} className="mr-2 text-purple-400 flex-shrink-0" />
          <span className="truncate" title={currentGoal}>Goal: {currentGoal}</span>
        </div>
      </div>

      {/* Collapsible Sources Section */}
      <div className="px-3 pt-2 pb-1 border-b border-neutral-700/90 bg-neutral-900/80">
        <button
          onClick={() => setIsSourcesOpen(!isSourcesOpen)}
          className="flex items-center justify-between w-full text-xs font-medium text-neutral-300 hover:text-neutral-100 focus:outline-none py-1"
          aria-expanded={isSourcesOpen}
          aria-controls="cited-sources-content"
        >
          <div className="flex items-center">
            {isSourcesOpen ? (
              <ChevronDown size={14} className="mr-1.5 flex-shrink-0" />
            ) : (
              <ChevronRight size={14} className="mr-1.5 flex-shrink-0" />
            )}
            Cited Sources ({sources.length})
          </div>
        </button>
        {isSourcesOpen && (
          <div id="cited-sources-content" className="mt-1.5 mb-1 max-h-32 overflow-y-auto custom-scrollbar-xs" ref={sourcesScrollRef}>
            {sources && sources.length > 0 ? (
              <ul className="space-y-1 text-xs">
                {sources.map((source, index) => (
                  <li key={source.url || `source-${index}`} className="truncate flex items-center group">
                    <span className="text-neutral-500 mr-1.5 pl-1">{source.citation_marker || `[${index+1}]`}</span>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 group-hover:text-blue-400 hover:underline flex-1 truncate"
                      title={source.url}
                    >
                      {source.title || source.url}
                    </a>
                    <LinkIcon size={10} className="ml-1 text-neutral-500 group-hover:text-blue-400 flex-shrink-0" />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-neutral-500 py-1 pl-1">
                No sources cited yet.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Thoughts Stream Section */}
      <ScrollArea className="flex-grow" viewportRef={thoughtsScrollRef}>
        <div className="px-3 py-2 space-y-1.5">
          {thoughts.map((thought) => (
            <CognitiveBlock key={thought.id} data={thought} />
          ))}
          {isLoadingNextThought && (
            <div className="flex items-center justify-center p-3 text-neutral-400 text-xs">
              <Loader2 size={16} className="animate-spin mr-2" />
              <span>AI is thinking...</span>
            </div>
          )}
          {!isLoadingNextThought && thoughts.length === 0 && (
            <div className="flex items-center justify-center p-3 text-neutral-500 text-xs">
              No thoughts to display yet.
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};
