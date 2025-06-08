export type ThoughtType = "Hypothesis" | "Action" | "Analysis" | "Strategy" | "Error";

export interface CognitiveBlockData {
  id: string; // Unique ID for each block
  type: ThoughtType;
  title: string; // e.g., "Initial Hypothesis", "Performing Web Search", "Analyzing Results"
  details?: string | string[]; // e.g., Search query, list of findings, or error message
  timestamp: string; // ISO string for when the thought was generated
}

export interface Source {
  title: string;
  url: string;
  citation_marker: string; // e.g., "[1]"
}

// For stream events that update parts of the overall state
export interface StreamedOverallState {
  current_goal?: string;
  // messages?: Message[]; // Assuming 'Message' type is from @langchain/langgraph-sdk
  // If full messages array is streamed this way. Usually, messagesKey handles this for useStream.
  // For now, focusing on current_goal and sources_gathered if they come via state_update.
  sources_gathered?: Source[];
}

export interface E2BArtifact {
  name: string;
  type: "image" | "html_content" | "other"; // Add more types as needed
  data_uri?: string; // For images (e.g., data:image/png;base64,...)
  content?: string;  // For HTML content string
  url?: string;      // If public URLs are ever used (not primary for this task)
}
