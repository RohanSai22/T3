import React, { useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Message } from "@langchain/langgraph-sdk";
import { Button } from "@/components/ui/button";
import { InputForm } from "./InputForm";
import { ThoughtStreamPanel } from "./ThoughtStreamPanel";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Source, E2BArtifact, CognitiveBlockData } from "@/types";
import { Copy, Check, AlertTriangle, Bot } from "lucide-react"; // Added Bot icon

interface ChatLayoutProps {
  messages: Message[];
  isLoading: boolean;
  onSubmit: (inputValue: string) => void;
  onCancel: () => void;
  researchMode: string;
  onResearchModeChange: (mode: string) => void;
  currentSources: Source[];
  e2bArtifacts: E2BArtifact[];
  thoughtStream: CognitiveBlockData[];
  isThinking: boolean; // isLoadingNextThought for ThoughtStreamPanel
  currentGoal: string;
}

export const ChatLayout: React.FC<ChatLayoutProps> = ({
  messages,
  isLoading,
  onSubmit,
  onCancel,
  researchMode,
  onResearchModeChange,
  currentSources,
  e2bArtifacts, // Will be used more in artifact rendering step
  thoughtStream,
  isThinking,
  currentGoal,
}) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [copyStates, setCopyStates] = React.useState<Record<string, boolean>>({});

  const handleCopy = (text: string, messageId: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopyStates((prev) => ({ ...prev, [messageId]: true }));
      setTimeout(() => {
        setCopyStates((prev) => ({ ...prev, [messageId]: false }));
      }, 1500);
    });
  };

  const lastHumanQuery = messages.filter((msg) => msg.type === "human").pop()?.content as string || "Your query";

  const renderSingleArtifact = (artifact: E2BArtifact, key?: string | number) => {
    const elementKey = key !== undefined ? `artifact-${artifact.name}-${key}` : `artifact-${artifact.name}`;
    if (artifact.type === "image" && artifact.data_uri) {
      return <img key={elementKey} src={artifact.data_uri} alt={artifact.name} className="max-w-full h-auto rounded-md my-2 border border-neutral-600" />;
    }
    if (artifact.type === "html_content" && artifact.content) {
      return (
        <iframe
          key={elementKey}
          srcDoc={artifact.content}
          title={artifact.name}
          className="w-full h-64 rounded-md my-2 border border-neutral-600 bg-white"
          sandbox="allow-scripts allow-same-origin"
        />
      );
    }
    return <p key={elementKey} className="text-xs text-neutral-400 my-1">Unsupported artifact: {artifact.name} ({artifact.type})</p>;
  };

  const processMessageContent = (content: string): (string | JSX.Element)[] => {
    const parts: (string | JSX.Element)[] = [];
    let lastIndex = 0;

    // Regex to find markers like [IMAGE: filename.png] or [HTML_OUTPUT: filename.html]
    const markerRegex = /\[(IMAGE|HTML_OUTPUT): ([^\]]+)\]/g;
    let match;

    while ((match = markerRegex.exec(content)) !== null) {
      const [fullMarker, type, name] = match;
      const markerIndex = match.index;

      // Add text part before the marker
      if (markerIndex > lastIndex) {
        parts.push(content.substring(lastIndex, markerIndex));
      }

      // Find and render artifact
      const artifact = e2bArtifacts.find(art => art.name === name.trim());
      if (artifact) {
        const artifactTypeMarker = type === "IMAGE" ? "image" : "html_content";
        if (artifact.type === artifactTypeMarker) {
          parts.push(renderSingleArtifact(artifact, `marker-${markerIndex}`));
        } else {
          parts.push(`[Unsupported artifact type for marker: ${name}]`);
        }
      } else {
        parts.push(`[Artifact not found: ${name}]`);
      }
      lastIndex = markerIndex + fullMarker.length;
    }

    // Add remaining text part
    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex));
    }
    return parts;
  };


  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      {/* Left Panel: Thought Stream and Last Query */}
      <aside className="w-[35%] max-w-md h-full border-r border-neutral-700 p-3 hidden md:flex md:flex-col gap-3 bg-neutral-800/60 backdrop-blur-sm">
        <div className="bg-neutral-900/70 p-3 rounded-lg shadow-inner border border-neutral-700/80">
          <h2 className="text-sm font-semibold text-neutral-300 mb-2 flex items-center">
            <Bot size={16} className="mr-2 text-purple-400" />
            Current Focus
          </h2>
          <p className="text-sm text-neutral-100 line-clamp-3" title={lastHumanQuery}>
            {lastHumanQuery}
          </p>
        </div>
        <ThoughtStreamPanel
          thoughts={thoughtStream}
          isLoadingNextThought={isThinking}
          currentGoal={currentGoal}
          sources={currentSources}
        />
      </aside>

      {/* Right Panel: Chat Messages and Input */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 p-4 pr-2" ref={scrollAreaRef}>
          <div className="space-y-6 max-w-3xl mx-auto w-full pb-4">
            {messages.map((msg, index) => (
              <div key={msg.id || `msg-${index}`} className={`flex flex-col ${msg.type === "human" ? "items-end" : "items-start"}`}>
                <div
                  className={`max-w-[85%] p-3 rounded-xl shadow ${
                    msg.type === "human"
                      ? "bg-blue-600 text-white rounded-br-none"
                      : "bg-neutral-700/60 text-neutral-100 rounded-bl-none border border-neutral-600/80"
                  }`}
                >
                  {msg.type === "ai" && msg.content.startsWith("Error:") && (
                    <div className="flex items-center text-red-400 mb-1">
                      <AlertTriangle size={16} className="mr-2" />
                      <span className="font-semibold">Error</span>
                    </div>
                  )}
                  {/* Process content for inline artifacts */}
                  {processMessageContent(msg.content as string).map((part, partIndex) =>
                    typeof part === 'string' ? (
                      <ReactMarkdown
                        key={`md-${msg.id || index}-part-${partIndex}`}
                        components={{
                          p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                          ol: ({ node, ...props }) => <ol className="list-decimal list-inside ml-4 mb-2" {...props} />,
                          ul: ({ node, ...props }) => <ul className="list-disc list-inside ml-4 mb-2" {...props} />,
                          li: ({ node, ...props }) => <li className="mb-0.5" {...props} />,
                          code: ({ node, inline, ...props }) =>
                            inline ? (
                              <code className="bg-neutral-900/80 text-orange-300 px-1 py-0.5 rounded text-sm" {...props} />
                            ) : (
                              <pre className="bg-neutral-900/80 p-2 rounded-md my-2 text-sm overflow-x-auto custom-scrollbar" {...props} />
                            ),
                          a: ({ node, ...props }) => <a className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                        }}
                      >
                        {part}
                      </ReactMarkdown>
                    ) : (
                      // This part is already a JSX element (rendered artifact)
                      part
                    )
                  )}
                  {msg.type === "ai" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="mt-2 h-7 w-7 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-600/50"
                      onClick={() => handleCopy(msg.content as string, msg.id || `msg-copy-${index}`)}
                      title="Copy message"
                    >
                      {copyStates[msg.id || `msg-copy-${index}`] ? <Check size={14} /> : <Copy size={14} />}
                    </Button>
                  )}
                </div>
                {/* The old artifact loop below is removed as artifacts are now processed inline */}
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="border-t border-neutral-700/80 p-3 bg-neutral-800/60 backdrop-blur-sm">
          <div className="max-w-3xl mx-auto w-full">
            <InputForm
              onSubmit={onSubmit}
              isLoading={isLoading}
              onCancel={onCancel}
              hasHistory={messages.length > 0}
              researchMode={researchMode}
              onResearchModeChange={onResearchModeChange}
            />
          </div>
        </div>
      </main>
    </div>
  );
};
