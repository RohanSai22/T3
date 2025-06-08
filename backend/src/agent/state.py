from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, List, Optional

from langgraph.graph import add_messages
from typing_extensions import Annotated, NotRequired
from pydantic import SkipValidation
import operator


class OverallState(TypedDict):
    messages: Annotated[list, add_messages]
    search_query: NotRequired[Annotated[list, operator.add]]
    query_list: NotRequired[list[Query]]
    web_research_result: NotRequired[Annotated[list, operator.add]]
    sources_gathered: NotRequired[Annotated[list, operator.add]]
    initial_search_query_count: NotRequired[int]
    max_research_loops: NotRequired[int]
    research_loop_count: NotRequired[int]
    number_of_ran_queries: NotRequired[int]
    is_sufficient: NotRequired[bool]
    knowledge_gap: NotRequired[str]
    follow_up_queries: NotRequired[Annotated[list, operator.add]]
    # E2B related fields - wrapped with SkipValidation to avoid Pydantic warnings
    e2b_artifact_urls: SkipValidation[List[str]]
    e2b_stdout: NotRequired[SkipValidation[List[str]]]
    e2b_stderr: NotRequired[SkipValidation[List[str]]]
    e2b_generated_code: NotRequired[SkipValidation[Optional[str]]]
    suggests_code_execution: NotRequired[SkipValidation[bool]]
    research_effort: NotRequired[SkipValidation[str]] # Added for routing logic
    # Citation mapping
    url_to_citation_marker: NotRequired[SkipValidation[dict[str, str]]] # Maps original URL to "[1]"
    next_citation_index: NotRequired[SkipValidation[int]]
    # Current goal for thought stream
    current_goal: NotRequired[SkipValidation[str]]
    # E2B artifacts data
    e2b_artifacts_data: NotRequired[SkipValidation[List[dict]]] # List of E2BArtifact-like dicts


class ReflectionState(TypedDict):
    is_sufficient: bool
    knowledge_gap: str
    follow_up_queries: NotRequired[Annotated[list, operator.add]]
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
