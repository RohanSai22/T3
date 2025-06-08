import os
import base64  # For encoding image data
import requests
import re
from urllib.parse import urlparse
from googlesearch import search as google_search_lib  # Importing the googlesearch library
from bs4 import BeautifulSoup
import spacy
from agent.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from google.genai import Client

from agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agent.configuration import Configuration, ResearchEffort
from agent.prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from e2b_code_interpreter.code_interpreter_sync import Sandbox as CodeInterpreter
from e2b_code_interpreter import Result as E2BResult
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any  # Added Dict, Any

from agent.prompts import e2b_code_generation_instructions
from agent.utils import (
    # get_citations, # Replaced by get_citations_from_response
    get_citations_from_response,
    get_research_topic,
    insert_citation_markers,
    # resolve_urls, # Removed
    create_thought_event, # Import the new helper
)

load_dotenv()

# Load spaCy model for NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy English model not found. Some NLP features may not work.")
    nlp = None

# Web scraping utility functions
def filter_urls(urls: List[str], query: str, max_results: int = 5) -> List[str]:
    """Filter URLs based on relevance to the query and remove unwanted domains."""
    
    # Domains to exclude
    excluded_domains = {
        'youtube.com', 'tiktok.com', 'instagram.com', 'facebook.com', 
        'twitter.com', 'x.com', 'reddit.com', 'linkedin.com',
        'pinterest.com', 'tumblr.com', 'snapchat.com'
    }
    
    # Keywords that indicate good content sources
    quality_indicators = [
        'wiki', 'edu', 'gov', 'org', 'research', 'study', 'analysis',
        'report', 'documentation', 'guide', 'tutorial', 'news'
    ]
    
    filtered_urls = []
    query_keywords = set(query.lower().split())
    
    for url in urls:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower().replace('www.', '')
        
        # Skip excluded domains
        if any(excluded in domain for excluded in excluded_domains):
            continue
            
        # Calculate relevance score
        score = 0
        url_lower = url.lower()
        
        # Check for query keywords in URL
        for keyword in query_keywords:
            if keyword in url_lower:
                score += 2
                
        # Check for quality indicators
        for indicator in quality_indicators:
            if indicator in url_lower:
                score += 1
                
        # Prefer certain domains
        if any(domain.endswith(tld) for tld in ['.edu', '.gov', '.org']):
            score += 3
            
        if score > 0:
            filtered_urls.append((url, score))
    
    # Sort by score and return top results
    filtered_urls.sort(key=lambda x: x[1], reverse=True)
    return [url for url, _ in filtered_urls[:max_results]]

def fetch_webpage_data(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Fetch and parse webpage content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        # Extract main content
        content = extract_text_from_html(soup)
        
        return {
            'url': url,
            'title': title_text,
            'content': content,
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'url': url,
            'title': 'Error fetching page',
            'content': f'Error: {str(e)}',
            'status': 'error'
        }

def extract_text_from_html(soup: BeautifulSoup) -> str:
    """Extract clean text content from HTML soup."""
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
        script.decompose()
    
    # Try to find main content areas first
    main_content = None
    for selector in ['main', 'article', '[role="main"]', '.content', '#content', '.post', '.entry']:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    if main_content:
        text = main_content.get_text()
    else:
        text = soup.get_text()
    
    # Clean up the text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    # Limit length to avoid excessive content
    if len(text) > 3000:
        text = text[:3000] + "..."
    
    return text

def is_related_content(text: str, query: str, threshold: float = 0.3) -> bool:
    """Check if the extracted text is related to the query using keyword matching."""
    if not nlp or not text or not query:
        return True  # If spaCy not available, assume relevant
    
    query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
    text_keywords = set(re.findall(r'\b\w+\b', text.lower()[:1000]))  # Check first 1000 chars
    
    if not query_keywords:
        return True
    
    overlap = len(query_keywords.intersection(text_keywords))
    relevance_score = overlap / len(query_keywords)
    
    return relevance_score >= threshold

def get_top_k_webpages_info(urls: List[str], query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Get information from top k most relevant webpages."""
    filtered_urls = filter_urls(urls, query, max_results=k*2)  # Get more than needed for filtering
    
    results = []
    for url in filtered_urls[:k]:  # Process only top k
        data = fetch_webpage_data(url)
        
        if data['status'] == 'success' and is_related_content(data['content'], query):
            results.append(data)
            
        if len(results) >= k:
            break
    
    return results


# Pydantic model for E2B Code Execution Request
class E2BCodeExecutionRequest(BaseModel):
    type: str = Field(description="Type of code: 'python', 'html', or 'none'")
    code: str = Field(description="The code to execute, or empty if type is 'none'")
    dependencies: Optional[List[str]] = Field(default_factory=list, description="List of pip packages to install for Python code.")
    rationale: str


if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Used for Google Search API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


# Nodes
# Note: All node functions that now use 'yield' will implicitly return a generator.
# LangGraph handles these generators to stream out yielded values and use the final 'return' for state updates.

def generate_query(state: OverallState, config: RunnableConfig) -> dict:
    """LangGraph node that generates search queries. Yields thoughts."""

    current_goal_message = "Generating initial search queries."
    # To update current_goal in UI *during* node execution, the event could be:
    # yield {"event_type": "current_goal", "data": current_goal_message }
    # For now, thoughts are yielded, and current_goal is updated in the dict returned by the node.
    yield {"event_type": "thought", "data": create_thought_event("Strategy", "Formulating Search Strategy", "Determining optimal search queries based on the user's request.")}

    configurable = Configuration.from_runnable_config(config)

    # number_of_initial_queries is now set by Configuration.model_post_init based on research_effort.
    # We use configurable.number_of_initial_queries directly for the prompt.
    # The state field initial_search_query_count might be redundant if not changed elsewhere.
    # For this call, we'll use the value from the config object.

    # init Gemini Flash
    try:
        llm = ChatGoogleGenerativeAI(
            model=configurable.query_generator_model,
            temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state.get("messages", [])), # Use .get()
        number_queries=configurable.number_of_initial_queries,
    )
    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)

    generated_queries = result.query if result and hasattr(result, 'query') else []

    query_list_details = [f"{i+1}. {q}" for i, q in enumerate(generated_queries)] if generated_queries else ["No queries generated."]
    yield {"event_type": "thought", "data": create_thought_event("Action", f"Generated {len(generated_queries)} initial search queries.", query_list_details)}

    return {
        "query_list": generated_queries,
        # Also pass research_effort from config to state, if not already there,
        # as it's needed by routing logic later.
        "research_effort": configurable.research_effort.value, # Pass enum's value (string)
        "max_research_loops": configurable.max_research_loops, # Pass this from config to state
        "initial_search_query_count": configurable.number_of_initial_queries, # Ensure this is in state
        "research_loop_count": 0, # Initialize loop counter
        "current_goal": "Initial queries generated. Starting web research."
    }
    except Exception as e:
        error_message = f"Error in generate_query: {str(e)}"
        print(error_message)
        yield {"event_type": "thought", "data": create_thought_event("Error", "Query Generation Failed", error_message)}
        return { # Return a valid state update with error indication
            "query_list": [],
            "research_effort": state.get("research_effort", ResearchEffort.NORMAL.value), # Keep existing or default
            "max_research_loops": state.get("max_research_loops", 1),
            "initial_search_query_count": 0,
            "research_loop_count": 0,
            "current_goal": "Failed to generate initial queries."
        }


def continue_to_web_research(state: dict): # state type here is from the output of generate_query (QueryGenerationState is too narrow now)
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    # The input 'state' to this conditional edge function is the output of 'generate_query'
    query_list = state.get("query_list", [])
    return [
        Send("web_research", {"search_query": search_query_item, "id": int(idx)})
        for idx, search_query_item in enumerate(query_list)
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> dict:
    """LangGraph node that performs web research. Yields thoughts."""
    search_query = state.get("search_query", "") # Use .get()
    node_id = state.get("id", "unknown_id") # Use .get()

    if not search_query:
        yield {"event_type": "thought", "data": create_thought_event("Error", "Web Search Skipped", "No search query provided.")}
        return {
            "sources_gathered": [],
            "search_query": [""],
            "web_research_result": ["Error: No search query provided."],
            "url_to_citation_marker": state.get("url_to_citation_marker", {}),
            "next_citation_index": state.get("next_citation_index", 1),
            "current_goal": "Web search skipped due to missing query."
        }

    yield {"event_type": "thought", "data": create_thought_event("Action", "Performing Web Search", f"Executing search for query: \"{search_query}\" (ID: {node_id})")}

    configurable = Configuration.from_runnable_config(config)

    # Initialize return fields
    combined_sources = []
    combined_snippets = []
    updated_marker_map = state.get("url_to_citation_marker", {})
    new_next_idx = state.get("next_citation_index", 1)

    try:
        formatted_prompt = web_searcher_instructions.format(
            current_date=get_current_date(),
            research_topic=search_query,
        )

        # Uses the google genai client
        response = genai_client.models.generate_content(
            model=configurable.query_generator_model,
            contents=formatted_prompt,
            config={
                "tools": [{"google_search": {}}],
                "temperature": 0,
            },
        )

        # Get citations, updated map, next index, and sources for this specific response
        textual_citations, updated_marker_map, new_next_idx, sources_for_this_call = get_citations_from_response(
            response,
            updated_marker_map, # Pass current map
            new_next_idx # Pass current index
        )

        # Insert citation markers ("[1]", "[2]", etc.) into the response text
        modified_text_genai = insert_citation_markers(response.text, textual_citations)
        combined_sources.extend(sources_for_this_call)
        combined_snippets.append(modified_text_genai)

    except Exception as e:
        error_msg = f"Error during Google Search API call for query '{search_query}': {str(e)}"
        print(error_msg)
        combined_snippets.append(f"Google Search API error for query '{search_query}': {error_msg}")
        yield {"event_type": "thought", "data": create_thought_event("Error", "Google Search API Error", error_msg)}

    # sources_for_this_call now contains dicts like {'title': ..., 'url': ..., 'short_url': '[1]'}
    # This will be added to the overall sources_gathered in the state.
    # Duplicates across different web_research calls will be handled by finalize_answer if necessary.

    # Enhanced Google Search with URL filtering and web scraping
    additional_sources = []
    additional_snippets = []
    
    try:
        yield {"event_type": "thought", "data": create_thought_event("Action", "Enhanced Google Search", f"Performing additional Google search with web scraping for: \"{search_query}\"")}
        
        # Get search results using googlesearch-python
        search_urls = list(google_search_lib(search_query, num_results=20, lang="en", sleep_interval=2.0)) # Consider making num_results configurable
        
        if search_urls:
            # Filter and scrape top URLs
            # Ensure k is configurable or a sensible default
            k_scrape = configurable.max_sources_per_query if hasattr(configurable, 'max_sources_per_query') else 3
            top_webpages = get_top_k_webpages_info(search_urls, search_query, k=k_scrape)
            
            scraped_count = 0
            for i, webpage_data in enumerate(top_webpages):
                if webpage_data.get('status') == 'success': # Use .get()
                    scraped_count +=1
                    # Create citation marker for this source
                    citation_key = f"gs_{node_id}_{i}" # Use node_id
                    
                    # Add to citation mapping
                    if webpage_data.get('url') not in updated_marker_map: # Use .get()
                        citation_marker = f"[{new_next_idx}]"
                        updated_marker_map[webpage_data.get('url')] = citation_marker # Use .get()
                        new_next_idx += 1
                    else:
                        citation_marker = updated_marker_map.get(webpage_data.get('url')) # Use .get()
                    
                    # Create source entry
                    source_entry = {
                        'title': webpage_data.get('title', 'No Title'), # Use .get()
                        'url': webpage_data.get('url'),
                        'citation_marker': citation_marker,
                        'segment_id': citation_key
                    }
                    combined_sources.append(source_entry) # Append to combined_sources directly
                    
                    # Create content snippet with citation
                    content_snippet = f"Title: {webpage_data.get('title', 'No Title')}\n" # Use .get()
                    content_snippet += f"Content: {webpage_data.get('content', '')}\n" # Use .get()
                    content_snippet += f"Source: {citation_marker} {webpage_data.get('url')}"
                    combined_snippets.append(content_snippet) # Append to combined_snippets
            
            yield {"event_type": "thought", "data": create_thought_event("Analysis", "Web Scraping Complete", f"Successfully processed {scraped_count} additional sources with content extraction and relevance filtering.")}
        else:
            yield {"event_type": "thought", "data": create_thought_event("Analysis", "Enhanced Google Search", "No URLs found from google_search_lib to scrape.")}

    except Exception as e:
        error_msg = f"Error during enhanced Google search/scraping for query '{search_query}': {str(e)}"
        print(error_msg)
        combined_snippets.append(f"Enhanced search/scraping error for query '{search_query}': {error_msg}") # Add to combined_snippets
        yield {"event_type": "thought", "data": create_thought_event("Error", "Enhanced Search/Scraping Error", error_msg)}

    # Update the state with the combined results from both search methods
    all_source_titles = [src.get('title', 'Unknown title') for src in combined_sources] # Use combined_sources
    details_text = f"Received {len(all_source_titles)} total search result snippets from multiple sources."
    # Limiting details to avoid excessive data in thought:
    if all_source_titles:
        details_text += " Example titles: " + ", ".join(all_source_titles[:3])
        if len(all_source_titles) > 3:
            details_text += "..."
    else:
        details_text = "No search results or snippets gathered."


    yield {"event_type": "thought", "data": create_thought_event("Analysis", f"Complete Web Search Results Analysis", f"Final analysis of all results for query \"{search_query}\". {details_text}")}

    return {
        "sources_gathered": combined_sources, # Use combined_sources
        "search_query": [search_query], # search_query is a string, ensure it's in a list if OverallState expects list
        "web_research_result": combined_snippets, # Use combined_snippets
        "url_to_citation_marker": updated_marker_map,
        "next_citation_index": new_next_idx,
        "current_goal": f"Enhanced web search for \"{search_query}\" complete. Reflecting on findings."
    }


def reflection(state: OverallState, config: RunnableConfig) -> dict: # Return type changed for yield
    """LangGraph node that reflects on information. Yields thoughts."""
    yield {"event_type": "thought", "data": create_thought_event("Strategy", "Assessing Information Gaps", "Analyzing current information to determine if it's sufficient or if further research or actions are needed.")}

    configurable = Configuration.from_runnable_config(config)
    # research_loop_count is passed in state, ensure it's incremented correctly for the current reflection.
    # The reflection node itself shouldn't mutate state["research_loop_count"] directly if it's an input,
    # but rather return the incremented value.
    # Let's assume research_loop_count is passed from the routing logic or previous step if it's stateful.
    # For this node, we'll calculate what its loop count *would be*.
    # The problem description implies state["research_loop_count"] is the one to use and update.

    current_loop_count = state.get("research_loop_count", 0) # Get current
    # This node's execution can be considered the start of a new loop count if it leads to more research/action.
    # Or, it's part of the ongoing loop_count. Let's assume it reports the count *for this reflection*.
    # The actual increment controlling max_loops happens in routing or by convention.
    # The original code: state["research_loop_count"] = state.get("research_loop_count", 0) + 1. This is a side effect.
    # Better to return the new value:
    research_loop_count_for_this_reflection = current_loop_count + 1 # This was already correct

    try:
        # Ensure reflection_model is used, not reasoning_model from a potentially outdated state key
        reflection_model_name = configurable.reflection_model

        # Format the prompt
        current_date = get_current_date()
        # Use .get() for state access
        research_topic = get_research_topic(state.get("messages", []))
        web_results = state.get("web_research_result", [])
        summaries_str = "\n\n---\n\n".join(web_results) if web_results else "No web research results available."

        formatted_prompt = reflection_instructions.format(
            current_date=current_date,
            research_topic=research_topic,
            summaries=summaries_str,
        )
        # init Reasoning Model
        llm = ChatGoogleGenerativeAI(
            model=reflection_model_name,
            temperature=1.0, # Consider if this should be configurable
            max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

        is_sufficient = result.is_sufficient if hasattr(result, 'is_sufficient') else False
        knowledge_gap = result.knowledge_gap if hasattr(result, 'knowledge_gap') else "No specific knowledge gap identified."
        follow_up_queries = result.follow_up_queries if hasattr(result, 'follow_up_queries') else []
        suggests_code_execution = result.suggests_code_execution if hasattr(result, 'suggests_code_execution') else False


        analysis_details = [
            f"Is information sufficient? {'Yes' if is_sufficient else 'No'}.",
            f"Identified knowledge gap: {knowledge_gap}"
        ]
        yield {"event_type": "thought", "data": create_thought_event("Analysis", "Reflection Results", analysis_details)}

        next_goal_for_state = "Next step determined based on reflection."
        if suggests_code_execution and os.getenv("E2B_API_KEY"): # Check API key before suggesting goal
            yield {"event_type": "thought", "data": create_thought_event("Strategy", "Code Execution Planned", "Planning to generate and execute code to address knowledge gap.")}
            next_goal_for_state = "Proceeding to code generation and execution."
        elif follow_up_queries:
            query_details = [f"{i+1}. {q}" for i, q in enumerate(follow_up_queries)]
            yield {"event_type": "thought", "data": create_thought_event("Action", f"Generated {len(follow_up_queries)} follow-up queries.", query_details)}
            next_goal_for_state = "Proceeding with follow-up web research."
        elif not is_sufficient:
            next_goal_for_state = "Information still insufficient, but no clear follow-up. Moving to finalize."
        else:
            next_goal_for_state = "Information deemed sufficient. Finalizing answer."

        new_total_queries = state.get("number_of_ran_queries", 0) + len(follow_up_queries)

        return {
            "is_sufficient": is_sufficient,
            "knowledge_gap": knowledge_gap,
            "follow_up_queries": follow_up_queries,
            "research_loop_count": research_loop_count_for_this_reflection,
            "suggests_code_execution": suggests_code_execution,
            "number_of_ran_queries": new_total_queries,
            "current_goal": next_goal_for_state
        }
    except Exception as e:
        error_message = f"Error in reflection: {str(e)}"
        print(error_message)
        yield {"event_type": "thought", "data": create_thought_event("Error", "Reflection Failed", error_message)}
        # Return a state that likely leads to finalization on error
        return {
            "is_sufficient": True, # Assume sufficient to stop further loops on error
            "knowledge_gap": "Error during reflection, unable to determine gap.",
            "follow_up_queries": [],
            "research_loop_count": research_loop_count_for_this_reflection, # Increment loop count
            "suggests_code_execution": False,
            "number_of_ran_queries": state.get("number_of_ran_queries", 0),
            "current_goal": "Error during reflection. Proceeding to finalize."
        }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> str:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_answer")
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Check if research is sufficient or if we've reached max loops
    if state.get("is_sufficient") or state.get("research_loop_count", 0) >= configurable.max_research_loops:
        return "finalize_answer"
    
    # Continue with more research if follow-up queries exist
    if state.get("follow_up_queries"):
        return "web_research"
    
    # Default to finalizing if no clear next step
    return "finalize_answer"

def route_after_reflection(state: OverallState) -> List[Send] | str:
    """
    Determines the next step after reflection:
    - Finalize if research is sufficient or max loops reached.
    - Execute E2B code if suggested and in 'Deep Research' effort.
    - Dispatch more web research queries if available.
    - Otherwise, finalize.
    """
    # config for max_research_loops is not directly available in state type,
    # but Configuration object is not passed here.
    # We need to retrieve max_loops. One way is to ensure it's in state from an earlier node,
    # or re-create a minimal config here if necessary.
    # For now, let's assume max_research_loops is correctly populated in the state.
    # The Configuration class now handles setting these based on research_effort in model_post_init.
    # So, if config is passed to reflection node, it should use the right max_loops.
    # The state should already have max_research_loops from the config used by a previous node.

    max_loops = state.get("max_research_loops")
    # Fallback if not in state (should ideally be there via Configuration)
    if max_loops is None:
        # This path suggests an issue with state propagation or initial config setup.
        # However, to make it robust, let's try to get it from a default config.
        # This is not ideal as it doesn't use runtime config.
        print("Warning: max_research_loops not found in state, using default from Configuration.")
        default_config = Configuration() # Gets default values
        max_loops = default_config.max_research_loops


    if state.get("is_sufficient") or state.get("research_loop_count", 0) >= max_loops:
        return "finalize_answer"

    # Check for E2B execution path
    # research_effort should be available in state if Configuration is used and propagated.
    # For now, assuming 'research_effort' might not be in OverallState directly.
    # The task implies 'research_effort' would be part of the config.
    # Let's assume 'suggests_code_execution' is the primary driver from reflection.
    # The condition "state.get("research_effort") == "Deep Research"" needs research_effort in state.
    # This is not added in step 2. This is a potential gap.
    # For now, I will rely only on suggests_code_execution.
    # If 'Deep Research' is a strict requirement, 'research_effort' needs to be added to OverallState
    # and populated from Configuration.

    # According to Configuration changes (Step 1 of previous task), research_effort is a field.
    # It's not added to OverallState in this task's Step 2. This needs to be reconciled.
    # I will assume research_effort IS in the state for now.
    # If not, this condition `state.get("research_effort") == ResearchEffort.DEEP_RESEARCH.value` will fail.
    # It was added to OverallState in a previous step.
    # We need to ensure that 'research_effort' in the state is populated from the Configuration
    # at the beginning of the graph execution or when configuration changes.

    # Check for E2B execution path
    should_execute_code = state.get("suggests_code_execution", False)
    current_research_effort = state.get("research_effort", ResearchEffort.NORMAL.value) # Default to NORMAL if not set

    if should_execute_code and current_research_effort == ResearchEffort.DEEP_RESEARCH.value:
        if not os.getenv("E2B_API_KEY"):
            print("Warning: E2B_API_KEY not set. Skipping code execution path. Will proceed to web research if queries exist, or finalize.")
            yield {"event_type": "thought", "data": create_thought_event("Warning", "E2B Execution Skipped", "E2B_API_KEY not set. Cannot execute code.")}
            # Fall through to web research or finalize logic
        else:
            # Yield thought before returning the node name string
            yield {"event_type": "thought", "data": create_thought_event("Routing", "Proceeding to Code Execution", "Reflection suggests code execution, API key is available, and effort is Deep Research.")}
            return "execute_e2b_code" # Correctly returns a string for the conditional edge

    follow_up_queries = state.get("follow_up_queries", [])
    if follow_up_queries:
        # `number_of_ran_queries` from reflection state now holds the total count *after* adding current follow_up_queries.
        # So, to get the base ID for this batch, we subtract the count of queries in this batch.
        id_base_for_dispatch = state.get("number_of_ran_queries", len(follow_up_queries)) - len(follow_up_queries)

        dispatches = []
        for i, f_query in enumerate(follow_up_queries):
            dispatches.append(Send("web_research", {"search_query": f_query, "id": id_base_for_dispatch + i}))
        return dispatches

    return "finalize_answer"


# Node for E2B Code Execution
def execute_e2b_code(state: OverallState, config: RunnableConfig) -> dict:
    """
    Executes code using E2B Code Interpreter. Yields thoughts.
    """
    yield {"event_type": "thought", "data": create_thought_event("Strategy", "E2B Code Generation", "Preparing to generate executable code based on reflection.")}

    e2b_updates = {
        "e2b_generated_code": None,
        "e2b_stdout": [],
        "e2b_stderr": [],
        "e2b_artifacts_data": [], # Changed from e2b_artifact_urls
        "suggests_code_execution": False,
        # current_goal will be updated based on outcome
    }

    configurable = Configuration.from_runnable_config(config)
    # Using query_generator_model for code generation, can be tuned.
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=0.4,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(E2BCodeExecutionRequest)

    research_topic = get_research_topic(state.get("messages", [])) # .get()
    # Ensure summaries and knowledge_gap are strings and not None
    summaries_str = "\n---\n\n".join(state.get("web_research_result", []) or []) # .get() with default list
    knowledge_gap_str = state.get("knowledge_gap", "No specific knowledge gap identified, general request.") # .get()


    prompt = e2b_code_generation_instructions.format(
        research_topic=research_topic,
        summaries=summaries_str,
        knowledge_gap=knowledge_gap_str,
    )

    try:
        llm_response = structured_llm.invoke(prompt)

        llm_code_type = getattr(llm_response, 'type', 'none')
        llm_code = getattr(llm_response, 'code', '')
        llm_dependencies = getattr(llm_response, 'dependencies', [])
        llm_rationale = getattr(llm_response, 'rationale', '')


        if llm_code_type == "none" or not llm_code:
            rationale = llm_rationale or "Code execution deemed not necessary by LLM or code is empty."
            e2b_updates["e2b_stderr"].append(rationale)
            yield {"event_type": "thought", "data": create_thought_event("Analysis", "Code Execution Skipped (LLM)", rationale)}
            e2b_updates["current_goal"] = "Skipped code execution based on LLM rationale. Reflecting again."
            return e2b_updates

        e2b_updates["e2b_generated_code"] = llm_code
        code_snippet = llm_code[:250] + "..." if len(llm_code) > 250 else llm_code
        yield {"event_type": "thought", "data": create_thought_event("Action", f"Generated {llm_code_type} code for E2B execution.", code_snippet)}

        # This check is technically redundant if route_after_reflection works correctly, but good for safety.
        if not os.getenv("E2B_API_KEY"):
            error_msg = "E2B_API_KEY is not set. Cannot execute code. This should have been caught by routing logic."
            print(f"ERROR: {error_msg}")
            e2b_updates["e2b_stderr"].append(error_msg)
            yield {"event_type": "thought", "data": create_thought_event("Error", "E2B API Key Missing (Execution Node)", error_msg)}
            e2b_updates["current_goal"] = "E2B execution failed (API Key missing). Reflecting again."
            return e2b_updates

        yield {"event_type": "thought", "data": create_thought_event("Action", "Executing Code in Sandbox", f"Running {llm_code_type} code in E2B sandbox.")}
        # Sandbox execution block
        try:
            with CodeInterpreter(api_key=os.getenv("E2B_API_KEY")) as sandbox:
                if llm_code_type == "python":
                    if llm_dependencies:
                        deps_str = ", ".join(llm_dependencies)
                        yield {"event_type": "thought", "data": create_thought_event("Action", "Installing Dependencies", f"Installing: {deps_str}")}
                        for dep_idx, dep in enumerate(llm_dependencies):
                            try:
                                install_result = sandbox.notebook.install_pip_package(dep)
                                if not install_result.success:
                                    err_detail = f"Failed to install dependency {dep_idx+1}/{len(llm_dependencies)}: {dep}. Error: {install_result.error}"
                                    e2b_updates["e2b_stderr"].append(err_detail)
                                    yield {"event_type": "thought", "data": create_thought_event("Error", f"Dependency Installation Failed: {dep}", err_detail)}
                            except Exception as e_dep:
                                 err_detail = f"Exception during dependency installation {dep}: {str(e_dep)}"
                                 e2b_updates["e2b_stderr"].append(err_detail)
                                 yield {"event_type": "thought", "data": create_thought_event("Error", f"Dependency Installation Exception: {dep}", err_detail)}
                    exec_result: E2BResult = sandbox.notebook.exec_cell(llm_code, timeout=120) # Configurable timeout
                elif llm_code_type == "html":
                    escaped_html_code = repr(llm_code)
                    python_code_for_html = f"with open('index.html', 'w', encoding='utf-8') as f: f.write({escaped_html_code})"
                    exec_result: E2BResult = sandbox.notebook.exec_cell(python_code_for_html, timeout=30) # Configurable timeout
                else:
                    err_detail = f"Unsupported code type for E2B: {llm_code_type}"
                    e2b_updates["e2b_stderr"].append(err_detail)
                    yield {"event_type": "thought", "data": create_thought_event("Error", "Unsupported E2B Code Type", err_detail)}
                    e2b_updates["current_goal"] = "E2B execution failed (Unsupported code type). Reflecting again."
                    return e2b_updates

                e2b_updates["e2b_stdout"] = [log.line for log in exec_result.logs.stdout]
                e2b_updates["e2b_stderr"].extend([log.line for log in exec_result.logs.stderr])

                if exec_result.error:
                    err_val = f"Name: {exec_result.error.name}\nValue: {exec_result.error.value}\nTraceback: {exec_result.error.traceback_raw}"
                    e2b_updates["e2b_stderr"].append(err_val) # Also add to stderr state
                    yield {"event_type": "thought", "data": create_thought_event("Error", "E2B Code Execution Error", err_val)}

                processed_artifacts_data = []
                artifact_names = []
                for art_idx, art in enumerate(exec_result.artifacts):
                    artifact_names.append(art.name)
                    try:
                        content_bytes = art.download_as_bytes()
                        if art.name.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                            mimetype = "image/png" # Default, can be refined
                            if art.name.lower().endswith((".jpg", ".jpeg")): mimetype = "image/jpeg"
                            elif art.name.lower().endswith(".gif"): mimetype = "image/gif"
                            content_base64 = base64.b64encode(content_bytes).decode('utf-8')
                            processed_artifacts_data.append({
                                "name": art.name, "type": "image",
                                "data_uri": f"data:{mimetype};base64,{content_base64}"})
                        elif art.name.lower().endswith(".html"):
                            try: html_content = art.download_as_string()
                            except AttributeError: html_content = content_bytes.decode('utf-8', errors='replace')
                            processed_artifacts_data.append({
                                "name": art.name, "type": "html_content", "content": html_content})
                        else: # Generic artifact
                            processed_artifacts_data.append({"name": art.name, "type": "other", "size_bytes": len(content_bytes)})
                    except Exception as art_e:
                        err_detail = f"Error processing artifact {art_idx+1}: {art.name}: {str(art_e)}"
                        e2b_updates["e2b_stderr"].append(err_detail)
                        yield {"event_type": "thought", "data": create_thought_event("Error", f"Artifact Processing Error: {art.name}", err_detail)}
                e2b_updates["e2b_artifacts_data"] = processed_artifacts_data
                analysis_details_list = [
                    f"Stdout lines: {len(e2b_updates['e2b_stdout'])}",
                    f"Stderr lines: {len(e2b_updates['e2b_stderr'])}",
                    f"Generated artifacts: {', '.join(artifact_names) if artifact_names else 'None'}"
                ]
                yield {"event_type": "thought", "data": create_thought_event("Analysis", "E2B Execution Outcome", analysis_details_list)}
        except Exception as sandbox_e: # Catch errors from CodeInterpreter context or setup
            err_msg = f"Error during E2B sandbox operation: {str(sandbox_e)}"
            print(err_msg)
            e2b_updates["e2b_stderr"].append(err_msg)
            yield {"event_type": "thought", "data": create_thought_event("Error", "E2B Sandbox Operation Failure", err_msg)}


    except Exception as e: # Catch errors from LLM call or other logic at the start of the node
        err_msg = f"Critical error in E2B node (before sandbox execution or during LLM call): {str(e)}"
        print(err_msg)
        e2b_updates["e2b_stderr"].append(err_msg)
        yield {"event_type": "thought", "data": create_thought_event("Error", "E2B Node Processing Failure", err_msg)}

    e2b_updates["current_goal"] = "Code execution process finished. Reflecting on E2B results."
    return e2b_updates


def finalize_answer(state: OverallState, config: RunnableConfig) -> dict: # Return type changed for yield
    """LangGraph node that finalizes the research summary. Yields thoughts."""
    yield {"event_type": "thought", "data": create_thought_event("Strategy", "Synthesizing Final Answer", "Preparing to generate the final comprehensive answer based on all gathered and processed information.")}

    configurable = Configuration.from_runnable_config(config)
    answer_model_name = configurable.answer_model # Ensure answer_model is used

    # Safely access all necessary state fields with defaults
    research_topic = get_research_topic(state.get("messages", []))
    web_research_results = state.get("web_research_result", [])
    summaries_str = "\n---\n\n".join(web_research_results) if web_research_results else "No web research information was gathered."

    e2b_generated_code_str = state.get("e2b_generated_code") or "No code was generated or executed."
    e2b_stdout_list = state.get("e2b_stdout", [])
    e2b_stdout_str = "\n".join(e2b_stdout_list) if e2b_stdout_list else "No standard output from code execution."
    e2b_stderr_list = state.get("e2b_stderr", [])
    e2b_stderr_str = "\n".join(e2b_stderr_list) if e2b_stderr_list else "No standard error from code execution."

    e2b_artifacts_data_list = state.get("e2b_artifacts_data", [])
    artifact_names_for_prompt = [art.get("name", "unknown_artifact") for art in e2b_artifacts_data_list]
    e2b_artifacts_str = ", ".join(artifact_names_for_prompt) if artifact_names_for_prompt else "No artifacts were produced by code execution."

    current_date = get_current_date()

    # Prepare a default error message if generation fails
    final_content = "Could not generate a final answer due to an error."
    final_sources_list = []

    try:
        # Format the prompt with safely accessed data
        formatted_prompt = answer_instructions.format(
            current_date=current_date,
            research_topic=research_topic,
            summaries=summaries_str,
            e2b_generated_code=e2b_generated_code_str,
            e2b_stdout_str=e2b_stdout_str,
            e2b_stderr_str=e2b_stderr_str,
            e2b_artifacts_str=e2b_artifacts_str,
        )

        llm = ChatGoogleGenerativeAI(
            model=answer_model_name,
            temperature=0, # Typically 0 for final answer generation
            max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        llm_response = llm.invoke(formatted_prompt)
        final_content = llm_response.content if hasattr(llm_response, 'content') else "LLM response was empty or malformed."

        yield {"event_type": "thought", "data": create_thought_event("Analysis", "Final Answer Generated", "The comprehensive answer has been composed.")}

        # Deduplicate and sort sources
        all_gathered_sources = state.get("sources_gathered", [])
        unique_sources_dict: Dict[str, Dict[str, Any]] = {}
        for source in all_gathered_sources:
            # Ensure source is a dict and has a 'url' key
            if isinstance(source, dict) and source.get("url"):
                if source["url"] not in unique_sources_dict:
                    unique_sources_dict[source["url"]] = source

        final_sources_list = list(unique_sources_dict.values())

        def get_marker_number(src):
            marker = src.get("citation_marker", "[99999]")
            try: return int(marker.strip("[]"))
            except ValueError: return 99999
        final_sources_list.sort(key=get_marker_number)

    except Exception as e:
        error_message = f"Error in finalize_answer: {str(e)}"
        print(error_message)
        yield {"event_type": "thought", "data": create_thought_event("Error", "Final Answer Generation Failed", error_message)}
        # final_content is already set to an error message
        # final_sources_list will be empty or whatever was processed before error

    return {
        "messages": [AIMessage(content=final_content)],
        "sources_gathered": final_sources_list, # Return processed list
        "e2b_artifacts_data": e2b_artifacts_data_list, # Pass through existing artifacts
        "current_goal": "Process complete. Final answer provided (or error occurred)."
    }


# Create our Agent Graph
builder = StateGraph(OverallState, config_schema=Configuration)

# Define the nodes we will cycle between
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("execute_e2b_code", execute_e2b_code) # New E2B node
builder.add_node("finalize_answer", finalize_answer)

# Set the entrypoint as `generate_query`
builder.add_edge(START, "generate_query")

# Add conditional edge to continue with search queries in a parallel branch
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"] # continue_to_web_research returns list of Sends
)

# After web research, go to reflection
builder.add_edge("web_research", "reflection")

# After reflection, decide where to go next
builder.add_conditional_edges(
    source="reflection",
    path=route_after_reflection, # This function returns node names or List[Send]
    # For List[Send], the target is implicit in the Send object.
    # For string node names, they must be keys in this map if a map is provided.
    # If route_after_reflection returns "web_research" directly, it's fine.
    # If it returns Send("web_research", ...), it's also fine.
    # The map is more for when the router function returns arbitrary keys that need mapping to node names.
    # Given route_after_reflection returns node names like "execute_e2b_code", "finalize_answer",
    # or a list of Sends to "web_research", this mapping should be:
    path_map={
        "execute_e2b_code": "execute_e2b_code",
        "finalize_answer": "finalize_answer",
        # "web_research" is handled by Send objects, so not strictly needed here if path returns Sends
        # However, if route_after_reflection could return the string "web_research", it would be needed.
        # Since it returns List[Send] for web_research, this map is mainly for the string return paths.
    }
)

# After E2B code execution, go back to reflection
builder.add_edge("execute_e2b_code", "reflection")

# Finalize the answer
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="pro-search-agent")
