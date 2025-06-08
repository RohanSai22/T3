import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { ThoughtStreamPanel } from "@/components/ThoughtStreamPanel"; // Import ThoughtStreamPanel
import { CognitiveBlockData, ThoughtType, Source, E2BArtifact } from "@/types"; // Import types
import { Button } from "@/components/ui/button"; // For mock button

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const [researchMode, setResearchMode] = useState<string>(() => {
    return localStorage.getItem("researchMode") || "Normal";
  });
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);

  // State for Thought Stream
  const [thoughtStream, setThoughtStream] = useState<CognitiveBlockData[]>([]);
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [currentGoal, setCurrentGoal] = useState<string>(
    "Ready for your request..."
  );
  const [currentSources, setCurrentSources] = useState<Source[]>([]);
  const [e2bArtifacts, setE2bArtifacts] = useState<E2BArtifact[]>([]); // New state for artifacts

  const handleStreamEvents = (eventDataChunk: any) => {
    // LangServe streams chunks. A chunk might be a dictionary representing a node's output,
    // or a part of it if the output itself is streamed.
    // We expect our "thought" events to be yielded by nodes.
    // LangServe's default streaming mode ('updates') wraps these in an 'ops' array.
    // Or, if it's configured for 'values' mode, it might be more direct.
    // The useStream hook might already parse this somewhat.
    // Let's assume eventDataChunk is the actual content yielded by a node or a state update object.

    console.log("Stream event:", eventDataChunk); // For debugging the structure

    if (eventDataChunk && typeof eventDataChunk === "object") {
      // Check for our custom thought event structure
      if (eventDataChunk.event_type === "thought" && eventDataChunk.data) {
        const thought = eventDataChunk.data as CognitiveBlockData;
        setThoughtStream((prevThoughts) => [...prevThoughts, thought]);
        // Update currentGoal if a thought specifically sets it (optional)
        // For instance, a "Strategy" thought might set the current goal.
        // setCurrentGoal(thought.title); // Example: make thought title the goal
        if (thought.type === "Error") {
          // setIsThinking(false); // Optional: stop "thinking" animation on error thought
        }
      }
      // Check for state updates (e.g., current_goal, or final sources_gathered if not handled by onFinish)
      // This part depends on how the backend structures these updates in the stream.
      // If the backend's final return (which becomes a state update) includes these fields:
      else if (
        eventDataChunk.current_goal ||
        eventDataChunk.sources_gathered ||
        eventDataChunk.messages
      ) {
        // This assumes that node outputs (which become state updates) are directly streamed.
        // The useStream hook with messagesKey="messages" might already handle messages separately.
        if (eventDataChunk.current_goal) {
          setCurrentGoal(eventDataChunk.current_goal);
        }
        if (eventDataChunk.sources_gathered) {
          // If sources_gathered comes before onFinish, update here.
          // However, onFinish is usually for the *final* state including all accumulated sources.
          setCurrentSources(eventDataChunk.sources_gathered as Source[]);
        }
        // If messages are also part of this chunk and not solely handled by messagesKey
        // if (eventDataChunk.messages) { /* update messages if needed */ }

        // Update the ProcessedEventsTimeline based on node names if they are keys in eventDataChunk
        // This is the existing logic from onUpdateEvent
        let processedEvent: ProcessedEvent | null = null;
        if (eventDataChunk.generate_query) {
          processedEvent = {
            title: "Generating Search Queries",
            data: eventDataChunk.generate_query.query_list.join(", "),
          };
        } else if (eventDataChunk.web_research) {
          const sources = eventDataChunk.web_research.sources_gathered || [];
          const numSources = sources.length;
          const uniqueLabels = [
            ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
          ];
          const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
          processedEvent = {
            title: "Web Research",
            data: `Gathered ${numSources} sources. Related to: ${
              exampleLabels || "N/A"
            }.`,
          };
        } else if (eventDataChunk.reflection) {
          processedEvent = {
            title: "Reflection",
            data: eventDataChunk.reflection.is_sufficient
              ? "Search successful, generating final answer."
              : `Need more information, searching for ${eventDataChunk.reflection.follow_up_queries.join(
                  ", "
                )}`,
          };
        } else if (eventDataChunk.finalize_answer) {
          processedEvent = {
            title: "Finalizing Answer",
            data: "Composing and presenting the final answer.",
          };
          hasFinalizeEventOccurredRef.current = true; // Keep this for historicalActivities logic
        }
        if (processedEvent) {
          setProcessedEventsTimeline((prevEvents) => [
            ...prevEvents,
            processedEvent!,
          ]);
        }
      }
      // Potentially handle other types of events if the backend sends more structures
    }
  };

  const thread = useStream<{
    messages: Message[]; // Handled by messagesKey
    research_effort: string;
    // These are top-level keys in the final graph state, potentially in onFinish's event.data
    sources_gathered?: Source[];
    current_goal?: string;
    e2b_artifacts_data?: E2BArtifact[]; // Expect this from backend
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : "http://localhost:8123",
    assistantId: "agent",
    messagesKey: "messages",
    onFinish: (event: any) => {
      console.log("Stream finished, final event data:", event);
      setIsThinking(false);
      if (event && event.data) {
        if (event.data.sources_gathered) {
          setCurrentSources(event.data.sources_gathered as Source[]);
        }
        if (event.data.e2b_artifacts_data) {
          setE2bArtifacts(event.data.e2b_artifacts_data as E2BArtifact[]);
        }
        if (event.data.current_goal) {
          setCurrentGoal(event.data.current_goal);
        } else {
          setCurrentGoal("Process finished.");
        }
      } else {
        setCurrentGoal("Process finished.");
      }
    },
    onUpdateEvent: handleStreamEvents, // Use the new consolidated handler
    onError: (error: any) => {
      console.error("Stream error:", error);
      setIsThinking(false);
      setCurrentGoal("An error occurred.");
      setThoughtStream((prevThoughts) => [
        ...prevThoughts,
        {
          id: Date.now().toString(),
          type: "Error",
          title: "Streaming Error",
          details:
            error.message || "An unspecified error occurred during streaming.",
          timestamp: new Date().toISOString(),
        },
      ]);
    },
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    async (submittedInputValue: string) => {
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      setCurrentSources([]);
      setE2bArtifacts([]); // Reset artifacts
      setThoughtStream([]);
      setCurrentGoal("Understanding your request...");
      setIsThinking(true);
      hasFinalizeEventOccurredRef.current = false;
      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      thread.submit({
        // This is the 'config' argument for the backend
        messages: newMessages,
        research_effort: researchMode, // researchMode from App.tsx's state
      });
    },
    [thread, researchMode] // Added researchMode as dependency
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  const handleResearchModeChange = (mode: string) => {
    setResearchMode(mode);
    localStorage.setItem("researchMode", mode);
  };

  // --- Temporary Mock Data Generation ---
  const mockThoughtTypes: ThoughtType[] = [
    "Hypothesis",
    "Action",
    "Analysis",
    "Strategy",
    "Error",
  ];
  const addMockThought = () => {
    setIsThinking(true);
    setCurrentGoal(`Processing step ${thoughtStream.length + 1}...`);
    setTimeout(() => {
      const randomType =
        mockThoughtTypes[Math.floor(Math.random() * mockThoughtTypes.length)];
      const mockThought: CognitiveBlockData = {
        id: Date.now().toString(),
        type: randomType,
        title: `${randomType} #${thoughtStream.length + 1}`,
        details:
          randomType === "Error"
            ? "Something went wrong during this step."
            : `Details for ${randomType} ${thoughtStream.length + 1}`,
        timestamp: new Date().toISOString(),
      };
      setThoughtStream((prev) => [...prev, mockThought]);
      setIsThinking(false);
    }, 1000);
  };
  // --- End Temporary Mock Data Generation ---

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      {/* Thought Stream Panel (Example Layout: Left Side) */}
      <aside className="w-1/3 h-full border-r border-neutral-700 p-2 hidden md:flex md:flex-col gap-2">
        {" "}
        {/* Added gap */}
        <ThoughtStreamPanel
          thoughts={thoughtStream}
          isLoadingNextThought={isThinking}
          currentGoal={currentGoal}
          sources={currentSources} // Pass currentSources
        />
        {/* Temporary button for mock data - can be removed later */}
        <Button
          onClick={addMockThought}
          className="mt-auto bg-blue-600 hover:bg-blue-700 text-white"
        >
          Add Mock Thought
        </Button>
      </aside>

      {/* Main Chat/Input Area (Example Layout: Right Side) */}
      <main className="flex-1 flex flex-col overflow-hidden max-w-4xl mx-auto w-full md:w-2/3">
        {" "}
        {/* Ensure this takes up remaining space */}
        <div
          className={`flex-1 overflow-y-auto ${
            thread.messages.length === 0 ? "flex" : ""
          }`}
        >
          {thread.messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={thread.isLoading}
              onCancel={handleCancel}
              researchMode={researchMode}
              onResearchModeChange={handleResearchModeChange}
              // WelcomeScreen doesn't need sources directly, InputForm within it doesn't use them
            />
          ) : (
            <ChatMessagesView
              messages={thread.messages}
              isLoading={thread.isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              researchMode={researchMode}
              onResearchModeChange={handleResearchModeChange}
              sources={currentSources}
              e2bArtifacts={e2bArtifacts} // Pass e2bArtifacts
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
            />
          )}
        </div>
      </main>
    </div>
  );
}
