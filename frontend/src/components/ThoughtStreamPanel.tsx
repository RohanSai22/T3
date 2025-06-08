import React, { useEffect, useRef, useState } from "react"; // Added useState
import { CognitiveBlockData, Source } from "@/types"; // Added Source
import { CognitiveBlock } from "./CognitiveBlock";
import { ChevronDown, ChevronRight } from "lucide-react"; // For icons

interface ThoughtStreamPanelProps {
  thoughts: CognitiveBlockData[];
  isLoadingNextThought: boolean;
  currentGoal: string;
  sources: Source[]; // Added sources prop
}

export const ThoughtStreamPanel: React.FC<ThoughtStreamPanelProps> = ({
  thoughts,
  isLoadingNextThought,
  currentGoal,
  sources,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isSourcesOpen, setIsSourcesOpen] = useState(true); // Default to open

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [thoughts, isLoadingNextThought]);

  return (
    // Panel uses bg-neutral-900, slightly darker than main App's bg-neutral-800
    <div className="thought-stream-panel bg-neutral-900 p-3 rounded-lg shadow-inner h-full flex flex-col text-neutral-100 border border-neutral-700">
      {/* Sticky Header for Goal and Sources */}
      <div className="sticky top-0 bg-neutral-900 pt-1 pb-2 z-10 border-b border-neutral-700 mb-3">
        <h2 className="text-md font-semibold text-neutral-100 mb-1 truncate">
          {" "}
          {/* Slightly smaller title, truncate */}
          Goal: <span className="text-blue-400 font-normal">{currentGoal}</span>
        </h2>
        <div className="sources-section">
          <button
            onClick={() => setIsSourcesOpen(!isSourcesOpen)}
            className="flex items-center justify-between w-full text-xs font-medium text-neutral-300 hover:text-neutral-100 focus:outline-none py-1"
          >
            <div className="flex items-center">
              {isSourcesOpen ? (
                <ChevronDown className="h-3 w-3 mr-1" />
              ) : (
                <ChevronRight className="h-3 w-3 mr-1" />
              )}
              Cited Sources ({sources.length})
            </div>
          </button>
          {isSourcesOpen && (
            <div className="mt-1 pl-3 pr-1 text-xs max-h-28 overflow-y-auto custom-scrollbar border-l-2 border-neutral-700">
              {" "}
              {/* Adjusted max-h */}
              {sources && sources.length > 0 ? (
                <ul className="space-y-0.5">
                  {sources.map((source) => (
                    <li
                      key={source.url}
                      className="truncate flex items-center group"
                    >
                      <span className="text-neutral-400 mr-1">
                        {source.citation_marker}
                      </span>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 group-hover:text-blue-400 hover:underline flex-1 truncate"
                        title={source.url}
                      >
                        {source.title || source.url}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-neutral-500 py-1">
                  No sources cited yet.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Thoughts Stream */}
      <div
        ref={scrollRef}
        className="flex-grow overflow-y-auto pr-1 space-y-1 custom-scrollbar"
      >
        {" "}
        {/* Adjusted padding/spacing */}
        {thoughts.map((thought) => (
          <CognitiveBlock key={thought.id} data={thought} />
        ))}
        {isLoadingNextThought && (
          <div className="flex items-center justify-center p-2 text-neutral-400">
            <span>AI is thinking...</span>
          </div>
        )}
      </div>
    </div>
  );
};
