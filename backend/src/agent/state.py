from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, List, Optional

from langgraph.graph import add_messages
from typing_extensions import Annotated, NotRequired
from pydantic import SkipValidation
import operator


class OverallState(TypedDict):
    messages: Annotated[list, add_messages]
    search_query: Annotated[list, operator.add]
    web_research_result: Annotated[list, operator.add]
    sources_gathered: Annotated[list, operator.add]
    initial_search_query_count: int
    max_research_loops: int
    research_loop_count: int
    # E2B related fields - wrapped with SkipValidation to avoid Pydantic warnings
    e2b_artifact_urls: SkipValidation[List[str]]
    e2b_stdout: SkipValidation[List[str]]
    e2b_stderr: SkipValidation[List[str]]
    e2b_generated_code: SkipValidation[Optional[str]]
    suggests_code_execution: SkipValidation[bool]
    research_effort: SkipValidation[str] # Added for routing logic
    # Citation mapping
    url_to_citation_marker: SkipValidation[dict[str, str]] # Maps original URL to "[1]"
    next_citation_index: SkipValidation[int]
    # Current goal for thought stream
    current_goal: SkipValidation[str]
    # E2B artifacts data
    e2b_artifacts_data: SkipValidation[List[dict]] # List of E2BArtifact-like dicts


class ReflectionState(TypedDict):
    is_sufficient: bool
    knowledge_gap: str
    follow_up_queries: Annotated[list, operator.add]
    research_loop_count: int
    number_of_ran_queries: int


class Query(TypedDict):
    query: str
    rationale: str


class QueryGenerationState(TypedDict):
    query_list: list[Query]


class WebSearchState(TypedDict):
    search_query: str
    id: str


@dataclass(kw_only=True)
class SearchStateOutput:
    running_summary: str = field(default=None)  # Final report
