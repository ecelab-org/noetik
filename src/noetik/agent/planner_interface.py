"""
Planner interface for Noetik.

This module is the only place that *directly* calls an LLM.  Everything else (agent loop, tools,
memory) stays model-agnostic.

We support two back-ends out of the box:

1. **OpenAI / Anthropic** via their REST APIs (requires env keys).
2. **Hugging Face Text-Generation-Inference (TGI)** for self-hosted models.

Additional providers can be added by subclassing :class:`BasePlanner` and registering via
:func:`register_planner`.
"""

import logging
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Tuple,
    Type,
)

import httpx
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
)

from noetik.agent.schema import ToolCall
from noetik.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models for response validation
class PlannerResponse(BaseModel):
    """Validates planner responses from LLMs."""

    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    answer: str | None = None


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------
_PLANNER_REGISTRY: dict[str, Type["BasePlanner"]] = {}


def register_planner(name: str) -> Callable:
    """Decorator to register a planner class under *name*."""

    def wrapper(cls: Type["BasePlanner"]) -> Type["BasePlanner"]:
        _PLANNER_REGISTRY[name] = cls
        return cls

    return wrapper


def load_planner(name: str | None = None) -> "BasePlanner":
    """
    Factory that returns an instantiated planner.

    Fallback order:
    1. *name* arg
    2. ``settings.PLANNER`` env/pyproject option
    3. default: ``"openai"``
    """

    target = name or getattr(settings, "PLANNER", "openai")
    cls = _PLANNER_REGISTRY.get(target.lower())  # type: ignore
    if cls is None:
        raise ValueError(f"Planner '{target}' is not registered.")
    return cls()


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------
class BasePlanner(ABC):
    """Abstract planner that converts user context -> tool calls / answer."""

    # Common system prompt for all planners
    SYSTEM_PROMPT: ClassVar[
        str
    ] = """\
You are Noetik, an autonomous AI assistant that can THINK and ACT.
When you need to use a tool, respond with JSON like:
{"tool": "<name>", "args": { ... }}
If no tool is needed, respond with:
{"answer": "<final reply to user>"}
Only one object, no extra text.
"""

    def _build_prompt(self, user_msg: str, available_tools: List[str] | None = None) -> str:
        """Build prompt with optional available tools information."""
        prompt = self.SYSTEM_PROMPT

        if available_tools:
            tools_str = ", ".join(available_tools)
            prompt += f"\n\nAvailable tools: {tools_str}"

        return prompt

    def _parse_response(self, content: str) -> Tuple[List[ToolCall], str | None]:
        """Parse and validate the LLM response using Pydantic."""
        try:
            parsed = PlannerResponse.model_validate_json(content)

            if parsed.tool_calls:
                calls = []
                for call in parsed.tool_calls:
                    if "name" in call:
                        calls.append(ToolCall(name=call["name"], args=call.get("args", {})))
                return calls, None
            return [], parsed.answer

        except ValidationError as e:
            logger.error("Failed to parse LLM response: %s", e)
            return [], f"Error parsing LLM response: {content}"

    @abstractmethod
    def plan(
        self, user_msg: str, available_tools: List[str] | None = None
    ) -> Tuple[List[ToolCall], str | None]:
        """Return tool calls + optional direct answer."""


# ---------------------------------------------------------------------------
# Concrete planners
# ---------------------------------------------------------------------------
@register_planner("tgi")
class TGIPlanner(BasePlanner):
    """TGI-based planner with httpx client and Pydantic validation."""

    def plan(
        self, user_msg: str, available_tools: List[str] | None = None
    ) -> Tuple[List[ToolCall], str | None]:
        """Call TGI endpoint and return tool calls + optional answer."""
        endpoint = getattr(settings, "TGI_ENDPOINT", "http://tgi:8080/generate")
        system_prompt = self._build_prompt(user_msg, available_tools)

        payload = {
            "inputs": f"{system_prompt}\n\nUser: {user_msg}",
            "parameters": {"max_new_tokens": 256, "temperature": 0.2, "stop": ["User:", "</s>"]},
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(endpoint, json=payload)
                resp.raise_for_status()
                content = resp.json()["generated_text"]

                logger.debug("TGI planner response: %s", content)
                return self._parse_response(content)

        except httpx.HTTPError as e:
            logger.error("TGI request error: %s", str(e))
            return [], f"Error calling TGI endpoint: {str(e)}"
        except Exception as e:  # pylint: disable=broad-except
            logger.error("TGI planner error: %s", str(e))
            return [], f"Error processing TGI response: {str(e)}"


@register_planner("openai")
class OpenAIPlanner(BasePlanner):
    """OpenAI-based planner with Pydantic validation."""

    def plan(
        self, user_msg: str, available_tools: List[str] | None = None
    ) -> Tuple[List[ToolCall], str | None]:
        import openai  # pylint: disable=import-outside-toplevel

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        system_prompt = self._build_prompt(user_msg, available_tools)

        try:
            resp = client.chat.completions.create(
                model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            content = resp.choices[0].message.content
            if not content:
                logger.error("OpenAI planner returned empty response")
                return [], "Error: Empty response from OpenAI"

            logger.debug("OpenAI planner response: %s", content)
            return self._parse_response(content)

        except Exception as e:
            logger.error("OpenAI planner error: %s", str(e))
            return [], f"Error calling OpenAI: {str(e)}"


@register_planner("anthropic")
class AnthropicPlanner(BasePlanner):
    """Anthropic Claude-based planner."""

    def plan(
        self, user_msg: str, available_tools: List[str] | None = None
    ) -> Tuple[List[ToolCall], str | None]:
        try:
            import anthropic  # pylint: disable=import-outside-toplevel

            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            system_prompt = self._build_prompt(user_msg, available_tools)

            response = client.messages.create(
                model=getattr(settings, "ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
                temperature=0.2,
            )

            # Handle different content block types from Anthropic API
            if response.content[0].type == "text":
                content = response.content[0].text
            else:
                # For non-text blocks, convert the block to a string representation
                content = str(response.content[0])

            logger.debug("Anthropic planner response: %s", content)
            return self._parse_response(content)

        except ImportError:
            logger.error("Anthropic SDK not installed")
            return [], "Error: Anthropic SDK not installed. Run 'pip install anthropic'"
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Anthropic planner error: %s", str(e))
            return [], f"Error calling Anthropic: {str(e)}"
