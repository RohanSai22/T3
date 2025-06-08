import os
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig


class ResearchEffort(str, Enum):
    NORMAL = "Normal"
    DEEP_RESEARCH = "Deep Research"


class Configuration(BaseModel):
    """The configuration for the agent."""

    query_generator_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the language model to use for the agent's query generation."
        },
    )

    reflection_model: str = Field(
        default="gemini-2.5-flash-preview-04-17",
        metadata={
            "description": "The name of the language model to use for the agent's reflection."
        },
    )

    answer_model: str = Field(
        default="gemini-2.5-pro-preview-05-06",
        metadata={
            "description": "The name of the language model to use for the agent's answer."
        },
    )

    research_effort: ResearchEffort = Field(
        default=ResearchEffort.NORMAL,
        metadata={"description": "The level of research effort to apply."},
    )

    number_of_initial_queries: int = Field(
        default=3,
        metadata={"description": "The number of initial search queries to generate."},
    )

    max_research_loops: int = Field(
        default=2,
        metadata={"description": "The maximum number of research loops to perform."},
    )

    def model_post_init(self, __context: Any) -> None:
        """Adjusts query and loop counts based on research effort."""
        if self.research_effort == ResearchEffort.DEEP_RESEARCH:
            self.number_of_initial_queries = 5
            self.max_research_loops = 4
        elif self.research_effort == ResearchEffort.NORMAL:
            # Keep defaults or set explicitly if they could be something else
            self.number_of_initial_queries = 3
            self.max_research_loops = 2
        # If more levels are added, handle them here

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)
