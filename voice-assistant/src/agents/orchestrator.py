"""
LangGraph Agent Orchestrator
Coordinates multiple agents using stateful graph-based workflows.
"""

import logging
import re
import time
from typing import Dict, List, Any, Optional, TypedDict
from enum import Enum

logger = logging.getLogger(__name__)

# Shared LLM instance for agents (lazy loaded)
_agent_llm = None


def _get_agent_llm():
    """Get or create the shared LLM instance for agent responses."""
    global _agent_llm
    if _agent_llm is None:
        try:
            from ..llm.qwen import get_llm
            _agent_llm = get_llm(engine="qwen3", model_size="1.7b", device="cpu")
        except Exception:
            try:
                from ..llm.qwen import get_llm
                _agent_llm = get_llm(engine="qwen", model_size="0.5b", device="cpu")
            except Exception as e:
                logger.error(f"Failed to load LLM for agents: {e}")
    return _agent_llm


class AgentState(TypedDict):
    """State passed between agents in the workflow."""
    user_input: str
    language: str
    intent: Optional[str]
    entities: List[Dict[str, Any]]
    agent_outputs: Dict[str, Any]
    final_response: Optional[str]
    error: Optional[str]


class IntentType(Enum):
    """Supported intent types."""
    INFORMATION_QUERY = "information_query"
    TASK_MANAGEMENT = "task_management"
    SMART_HOME = "smart_home"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"


# System prompts for each agent role
AGENT_PROMPTS = {
    "info_agent": (
        "You are an information assistant specializing in answering questions. "
        "Provide accurate, concise answers in 1-3 sentences. "
        "If you don't know something, say so honestly."
    ),
    "task_agent": (
        "You are a task management assistant. Help users with reminders, "
        "scheduling, and to-do items. Confirm what you've noted and provide "
        "a brief, helpful response in 1-2 sentences."
    ),
    "chat_agent": (
        "You are a friendly conversational assistant. Be warm, natural, "
        "and concise. Respond in 1-3 sentences as if speaking to someone."
    ),
}

# Smart fallback responses when LLM is not available
FALLBACK_RESPONSES = {
    IntentType.INFORMATION_QUERY: [
        "I'd love to help answer that question. My knowledge system is currently loading — please try again in a moment.",
        "That's a great question! The information module is still initializing. Give me a moment.",
    ],
    IntentType.TASK_MANAGEMENT: [
        "I've noted your request. The task management system is starting up — I'll be fully ready shortly.",
        "Got it! I'll set that up for you once the task system finishes loading.",
    ],
    IntentType.GENERAL_CHAT: [
        "Thanks for chatting with me! I'm still warming up my language model, but I'll be fully conversational in a moment.",
        "Hello! I'm currently initializing. I'll be ready for a proper conversation shortly.",
    ],
    IntentType.UNKNOWN: [
        "I received your message. My systems are still starting up — please try again in a moment.",
    ],
}

_fallback_counter = 0


def _strip_think_tags(text: str) -> str:
    """Strip Qwen3's <think>...</think> reasoning blocks from output."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()


def _get_fallback(intent: IntentType) -> str:
    """Get a rotating fallback response for the given intent."""
    global _fallback_counter
    responses = FALLBACK_RESPONSES.get(intent, FALLBACK_RESPONSES[IntentType.UNKNOWN])
    resp = responses[_fallback_counter % len(responses)]
    _fallback_counter += 1
    return resp


class AgentOrchestrator:
    """
    LangGraph-based orchestrator for managing multiple specialized agents.

    Implements a stateful graph workflow where:
    1. User input is analyzed for intent
    2. Appropriate agent(s) are selected
    3. Agents execute their tasks using the LLM
    4. Results are aggregated and returned
    """

    def __init__(self, config: Optional[Dict] = None, llm=None):
        """
        Initialize the orchestrator.

        Args:
            config: Optional configuration dictionary
            llm: Optional LLM instance (QwenLLM or Qwen3LLM) for generating responses
        """
        self.config = config or {}
        self.graph = None
        self.agents = {}
        self.llm = llm

    def setup(self):
        """Setup the LangGraph workflow."""
        try:
            from langgraph.graph import StateGraph, END

            workflow = StateGraph(AgentState)

            workflow.add_node("intent_classifier", self._classify_intent)
            workflow.add_node("info_agent", self._run_info_agent)
            workflow.add_node("task_agent", self._run_task_agent)
            workflow.add_node("chat_agent", self._run_chat_agent)
            workflow.add_node("response_generator", self._generate_response)

            workflow.set_entry_point("intent_classifier")

            workflow.add_conditional_edges(
                "intent_classifier",
                self._route_to_agent,
                {
                    IntentType.INFORMATION_QUERY.value: "info_agent",
                    IntentType.TASK_MANAGEMENT.value: "task_agent",
                    IntentType.GENERAL_CHAT.value: "chat_agent",
                    IntentType.UNKNOWN.value: "chat_agent",
                }
            )

            workflow.add_edge("info_agent", "response_generator")
            workflow.add_edge("task_agent", "response_generator")
            workflow.add_edge("chat_agent", "response_generator")
            workflow.add_edge("response_generator", END)

            self.graph = workflow.compile()
            logger.info("Agent orchestrator setup complete (LangGraph)")

        except ImportError:
            logger.warning("LangGraph not installed. Using simple orchestration.")
            self._setup_simple_orchestrator()

    def _setup_simple_orchestrator(self):
        """Fallback simple orchestrator without LangGraph."""
        logger.info("Using simple orchestrator fallback")
        self.graph = None

    def _llm_respond(self, user_input: str, agent_name: str) -> str:
        """
        Generate a response using the LLM with the agent's system prompt.

        Falls back to smart contextual responses if LLM is not available.
        """
        if self.llm is None:
            intent_map = {
                "info_agent": IntentType.INFORMATION_QUERY,
                "task_agent": IntentType.TASK_MANAGEMENT,
                "chat_agent": IntentType.GENERAL_CHAT,
            }
            return _get_fallback(intent_map.get(agent_name, IntentType.UNKNOWN))

        try:
            # Temporarily set agent-specific system prompt
            original_prompt = self.llm.system_prompt
            self.llm.set_system_prompt(AGENT_PROMPTS.get(agent_name, original_prompt))

            response = self.llm.chat(user_input, remember=True)

            # Restore original prompt
            self.llm.set_system_prompt(original_prompt)

            return _strip_think_tags(response.content)

        except Exception as e:
            logger.error(f"LLM generation failed in {agent_name}: {e}")
            intent_map = {
                "info_agent": IntentType.INFORMATION_QUERY,
                "task_agent": IntentType.TASK_MANAGEMENT,
                "chat_agent": IntentType.GENERAL_CHAT,
            }
            return _get_fallback(intent_map.get(agent_name, IntentType.UNKNOWN))

    def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify user intent from input."""
        user_input = state["user_input"].lower()

        if any(word in user_input for word in [
            "what", "who", "where", "when", "how", "why", "tell me",
            "explain", "describe", "define", "meaning",
        ]):
            intent = IntentType.INFORMATION_QUERY.value
        elif any(word in user_input for word in [
            "remind", "schedule", "task", "todo", "calendar", "alarm",
            "set", "timer", "appointment", "meeting",
        ]):
            intent = IntentType.TASK_MANAGEMENT.value
        elif any(word in user_input for word in [
            "light", "fan", "ac", "door", "temperature", "switch",
            "turn on", "turn off",
        ]):
            intent = IntentType.SMART_HOME.value
        else:
            intent = IntentType.GENERAL_CHAT.value

        state["intent"] = intent
        logger.info(f"Classified intent: {intent}")
        return state

    def _route_to_agent(self, state: AgentState) -> str:
        """Route to appropriate agent based on intent."""
        return state.get("intent", IntentType.UNKNOWN.value)

    def _run_info_agent(self, state: AgentState) -> AgentState:
        """Run the information query agent with LLM."""
        logger.info("Running info agent")
        response = self._llm_respond(state["user_input"], "info_agent")

        state["agent_outputs"]["info_agent"] = {
            "response": response,
            "sources": [],
        }
        return state

    def _run_task_agent(self, state: AgentState) -> AgentState:
        """Run the task management agent with LLM."""
        logger.info("Running task agent")
        response = self._llm_respond(state["user_input"], "task_agent")

        state["agent_outputs"]["task_agent"] = {
            "response": response,
            "task_created": True,
        }
        return state

    def _run_chat_agent(self, state: AgentState) -> AgentState:
        """Run the general chat agent with LLM."""
        logger.info("Running chat agent")
        response = self._llm_respond(state["user_input"], "chat_agent")

        state["agent_outputs"]["chat_agent"] = {
            "response": response,
        }
        return state

    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response from agent outputs."""
        outputs = state.get("agent_outputs", {})

        responses = []
        for agent_name, output in outputs.items():
            if "response" in output:
                responses.append(output["response"])

        state["final_response"] = " ".join(responses) if responses else "I couldn't process your request."
        return state

    def process(self, user_input: str, language: str = "en") -> Dict[str, Any]:
        """
        Process user input through the agent workflow.

        Args:
            user_input: User's text input
            language: Language code

        Returns:
            Dictionary with response and metadata
        """
        initial_state: AgentState = {
            "user_input": user_input,
            "language": language,
            "intent": None,
            "entities": [],
            "agent_outputs": {},
            "final_response": None,
            "error": None,
        }

        start = time.perf_counter()

        if self.graph:
            result = self.graph.invoke(initial_state)
        else:
            # Simple fallback processing
            result = self._classify_intent(initial_state)
            intent = result.get("intent", IntentType.GENERAL_CHAT.value)

            if intent == IntentType.INFORMATION_QUERY.value:
                result = self._run_info_agent(result)
            elif intent == IntentType.TASK_MANAGEMENT.value:
                result = self._run_task_agent(result)
            else:
                result = self._run_chat_agent(result)

            result = self._generate_response(result)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"Orchestrator processed in {elapsed:.1f}ms")

        # Determine which agent handled the request
        agent_outputs = result.get("agent_outputs", {})
        active_agent = list(agent_outputs.keys())[0] if agent_outputs else "unknown"

        return {
            "response": result.get("final_response", ""),
            "intent": result.get("intent"),
            "language": result.get("language"),
            "agent": active_agent,
            "llm_time_ms": elapsed,
        }


# Example usage and testing
def demo():
    """Demo function showing orchestrator usage."""
    orchestrator = AgentOrchestrator()
    orchestrator.setup()

    test_queries = [
        "What is the weather today?",
        "Remind me to call mom at 5pm",
        "Turn on the living room lights",
        "Hello, how are you?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        result = orchestrator.process(query)
        print(f"Intent: {result['intent']}")
        print(f"Response: {result['response']}")


if __name__ == "__main__":
    demo()
