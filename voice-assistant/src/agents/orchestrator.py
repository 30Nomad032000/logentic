"""
LangGraph Agent Orchestrator
Coordinates multiple agents using stateful graph-based workflows.
"""

import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from enum import Enum

logger = logging.getLogger(__name__)


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


class AgentOrchestrator:
    """
    LangGraph-based orchestrator for managing multiple specialized agents.

    Implements a stateful graph workflow where:
    1. User input is analyzed for intent
    2. Appropriate agent(s) are selected
    3. Agents execute their tasks
    4. Results are aggregated and returned
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the orchestrator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.graph = None
        self.agents = {}

    def setup(self):
        """Setup the LangGraph workflow."""
        try:
            from langgraph.graph import StateGraph, END

            # Create the state graph
            workflow = StateGraph(AgentState)

            # Add nodes (processing steps)
            workflow.add_node("intent_classifier", self._classify_intent)
            workflow.add_node("info_agent", self._run_info_agent)
            workflow.add_node("task_agent", self._run_task_agent)
            workflow.add_node("chat_agent", self._run_chat_agent)
            workflow.add_node("response_generator", self._generate_response)

            # Set entry point
            workflow.set_entry_point("intent_classifier")

            # Add conditional edges based on intent
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

            # All agents lead to response generator
            workflow.add_edge("info_agent", "response_generator")
            workflow.add_edge("task_agent", "response_generator")
            workflow.add_edge("chat_agent", "response_generator")

            # Response generator ends the workflow
            workflow.add_edge("response_generator", END)

            # Compile the graph
            self.graph = workflow.compile()
            logger.info("Agent orchestrator setup complete")

        except ImportError:
            logger.warning("LangGraph not installed. Using simple orchestration.")
            self._setup_simple_orchestrator()

    def _setup_simple_orchestrator(self):
        """Fallback simple orchestrator without LangGraph."""
        logger.info("Using simple orchestrator fallback")
        self.graph = None

    def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify user intent from input."""
        user_input = state["user_input"].lower()

        # Simple keyword-based classification (replace with ML model in production)
        if any(word in user_input for word in ["what", "who", "where", "when", "how", "why", "tell me"]):
            intent = IntentType.INFORMATION_QUERY.value
        elif any(word in user_input for word in ["remind", "schedule", "task", "todo", "calendar"]):
            intent = IntentType.TASK_MANAGEMENT.value
        elif any(word in user_input for word in ["light", "fan", "ac", "door", "temperature"]):
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
        """Run the information query agent."""
        logger.info("Running info agent")
        user_input = state["user_input"]

        # Placeholder - integrate with actual knowledge base/search
        response = f"[Info Agent] Processing query: {user_input}"

        state["agent_outputs"]["info_agent"] = {
            "response": response,
            "sources": [],
        }
        return state

    def _run_task_agent(self, state: AgentState) -> AgentState:
        """Run the task management agent."""
        logger.info("Running task agent")
        user_input = state["user_input"]

        # Placeholder - integrate with actual task/calendar system
        response = f"[Task Agent] Processing task request: {user_input}"

        state["agent_outputs"]["task_agent"] = {
            "response": response,
            "task_created": False,
        }
        return state

    def _run_chat_agent(self, state: AgentState) -> AgentState:
        """Run the general chat agent."""
        logger.info("Running chat agent")
        user_input = state["user_input"]

        # Placeholder - integrate with LLM for conversation
        response = f"[Chat Agent] I understand you said: {user_input}"

        state["agent_outputs"]["chat_agent"] = {
            "response": response,
        }
        return state

    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response from agent outputs."""
        outputs = state.get("agent_outputs", {})

        # Combine responses from all agents that ran
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

        if self.graph:
            # Run through LangGraph
            result = self.graph.invoke(initial_state)
        else:
            # Simple fallback processing
            result = self._classify_intent(initial_state)
            result = self._run_chat_agent(result)
            result = self._generate_response(result)

        return {
            "response": result.get("final_response", ""),
            "intent": result.get("intent"),
            "language": result.get("language"),
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
