from typing import Any, Dict, List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage


def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    Get the research topic from the messages.
    """
    # check if request has a history and combine the messages into a single string
    if len(messages) == 1:
        research_topic = messages[-1].content
    else:
        research_topic = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                research_topic += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                research_topic += f"Assistant: {message.content}\n"
    return research_topic


# resolve_urls is removed as its specific short URL format is no longer needed.
# The new system maps original URLs directly to "[N]" citation markers.

def insert_citation_markers(text: str, citations_list: List[Dict[str, Any]]) -> str:
    """
    Inserts citation markers into a text string based on start and end indices.

    Args:
        text (str): The original text string.
        citations_list (list): A list of dictionaries, where each dictionary
                               contains 'start_index', 'end_index', and
                               'segment_string' (the marker to insert).
                               Indices are assumed to be for the original text.

    Returns:
        str: The text with citation markers inserted.
    """
    # Sort citations by end_index in descending order.
    # If end_index is the same, secondary sort by start_index descending.
    # This ensures that insertions at the end of the string don't affect
    # the indices of earlier parts of the string that still need to be processed.
    sorted_citations = sorted(
        citations_list, key=lambda c: (c["end_index"], c["start_index"]), reverse=True
    )

    modified_text = text
    for citation_info in sorted_citations:
        end_idx = citation_info["end_index"]
        # marker_to_insert will be a concatenation of markers like "[1] [2]"
        # if multiple sources back the same text segment.
        marker_to_insert = ""
        seen_markers_for_segment = set()
        for segment in citation_info["segments"]:
            if segment['marker'] not in seen_markers_for_segment:
                marker_to_insert += f" {segment['marker']}" # Add space before marker
                seen_markers_for_segment.add(segment['marker'])

        if marker_to_insert: # Only insert if there are actual markers
            modified_text = (
                modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
            )

    return modified_text


def get_citations_from_response(
    response: Any, # Gemini response object
    url_to_citation_marker_map: Dict[str, str],
    current_next_citation_index: int
) -> tuple[List[Dict[str, Any]], Dict[str, str], int, List[Dict[str, str]]]:
    """
    Extracts and formats citation information from a Gemini model's response.
    Updates and uses a global mapping from original URLs to simple numeric markers (e.g., "[1]").

    Args:
        response: The response object from the Gemini model.
        url_to_citation_marker_map: Current dictionary mapping URLs to their "[N]" markers.
        current_next_citation_index: The next available integer for citation markers.

    Returns:
        A tuple containing:
        - textual_citations_list (list): List of dicts for insert_citation_markers,
                                         each with start_index, end_index, and a list of segments
                                         (where each segment has a 'marker' key).
        - updated_url_to_citation_marker_map (dict): The updated mapping.
        - new_next_citation_index (int): The next citation index to be used.
        - sources_for_state (list): List of unique source dicts ({title, url, marker})
                                    for storage in OverallState.sources_gathered.
    """
    textual_citations_list = []
    processed_sources_for_state = []

    # Ensure response and necessary nested structures are present
    if not response or not response.candidates:
        return textual_citations_list, url_to_citation_marker_map, current_next_citation_index, processed_sources_for_state

    candidate = response.candidates[0]
    if (
        not hasattr(candidate, "grounding_metadata")
        or not candidate.grounding_metadata
        or not hasattr(candidate.grounding_metadata, "grounding_supports")
    ):
        return textual_citations_list, url_to_citation_marker_map, current_next_citation_index, processed_sources_for_state

    # Create a temporary set to track unique sources added in this call to avoid duplicates in processed_sources_for_state
    # This is important because url_to_citation_marker_map is global and persists across calls.
    unique_urls_this_call = set()

    for support in candidate.grounding_metadata.grounding_supports:
        textual_citation_segment_info = {}

        if not hasattr(support, "segment") or support.segment is None:
            continue
        start_index = support.segment.start_index if support.segment.start_index is not None else 0
        if support.segment.end_index is None:
            continue

        textual_citation_segment_info["start_index"] = start_index
        textual_citation_segment_info["end_index"] = support.segment.end_index
        textual_citation_segment_info["segments"] = []

        if hasattr(support, "grounding_chunk_indices") and support.grounding_chunk_indices:
            for ind in support.grounding_chunk_indices:
                try:
                    chunk = candidate.grounding_metadata.grounding_chunks[ind]
                    original_url = chunk.web.uri
                    title = chunk.web.title or original_url # Use URL if title is empty

                    if original_url not in url_to_citation_marker_map:
                        marker = f"[{current_next_citation_index}]"
                        url_to_citation_marker_map[original_url] = marker
                        current_next_citation_index += 1
                    else:
                        marker = url_to_citation_marker_map[original_url]

                    # For textual insertion (e.g. "[1]")
                    textual_citation_segment_info["segments"].append({'marker': marker})

                    # For overall state sources_gathered
                    if original_url not in unique_urls_this_call:
                        processed_sources_for_state.append({
                            "title": title,
                            "url": original_url,
                            "citation_marker": marker, # Changed from short_url to citation_marker
                        })
                        unique_urls_this_call.add(original_url)
                except (IndexError, AttributeError):
                    pass # Skip problematic chunks

        if textual_citation_segment_info["segments"]: # Only add if there are valid segments
            textual_citations_list.append(textual_citation_segment_info)

    return textual_citations_list, url_to_citation_marker_map, current_next_citation_index, processed_sources_for_state


# Helper function for creating thought events
import uuid
from datetime import datetime, timezone

def create_thought_event(type: str, title: str, details: Any = None) -> Dict[str, Any]:
    """
    Creates a dictionary structured like CognitiveBlockData for streaming.
    Ensures details are serializable (e.g., converts lists/dicts to strings if necessary,
    though details can be string | string[] as per CognitiveBlockData).
    """
    # Ensure details are serializable; for now, assuming direct pass-through
    # if details is already string or List[str]. Complex objects might need explicit serialization.
    if isinstance(details, (list, dict)) and not all(isinstance(item, str) for item in details if isinstance(details, list)):
        # Example: convert non-string list items to string; or handle dicts
        # For this task, we'll assume details will be provided appropriately by nodes.
        pass

    return {
        # This is the inner data structure, to be wrapped if needed for distinguishing event types
        "id": str(uuid.uuid4()),
        "type": type,
        "title": title,
        "details": details if details is not None else "", # Ensure details is not None
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
