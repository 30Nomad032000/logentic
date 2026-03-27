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
        "You are an information assistant. Answer questions accurately and "
        "concisely in 1-3 sentences. Do NOT include your reasoning or thought "
        "process in the response. Only output the final answer."
    ),
    "task_agent": (
        "You are a task management assistant. When the user asks to set a "
        "reminder, alarm, timer, or to-do, reply with a short confirmation. "
        "Example: 'Done! Alarm set for 5:00 AM.' "
        "Do NOT include reasoning, thoughts, or follow-up questions. "
        "Just confirm the task in 1 sentence."
    ),
    "chat_agent": (
        "You are a friendly conversational assistant. Respond naturally in "
        "1-3 sentences. Do NOT include your reasoning or thought process. "
        "Only output the final response."
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
    # Remove complete <think>...</think> pairs
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove unclosed <think> tags (LLM hit max tokens mid-thought)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


def _extract_thinking(text: str) -> str:
    """Extract the content of <think>...</think> blocks from LLM output."""
    # Match complete pairs
    matches = re.findall(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    if matches:
        return "\n".join(m.strip() for m in matches)
    # Match unclosed tag (LLM hit max tokens mid-thought)
    unclosed = re.search(r"<think>(.*)", text, flags=re.DOTALL)
    if unclosed:
        return unclosed.group(1).strip()
    return ""


# Patterns that indicate the LLM is reasoning out loud instead of answering
_REASONING_PATTERNS = [
    r"^(okay|ok|alright|let me|hmm|so),?\s*(the user|i need|i should|let me|i'll|looking)",
    r"^(the user (is asking|wants|said|asked|mentioned))",
    r"(i need to|i should|let me check|let me think|wait,)",
    r"(previous message|previous interaction|earlier.*asked)",
]
_REASONING_RE = re.compile("|".join(_REASONING_PATTERNS), re.IGNORECASE)


def _is_reasoning_leak(text: str) -> bool:
    """Detect if the LLM output is chain-of-thought reasoning rather than a real answer."""
    # Short responses are likely real answers
    if len(text) < 80:
        return False
    return bool(_REASONING_RE.search(text))


def _extract_final_answer(text: str) -> str:
    """Try to extract the actual answer from reasoning-contaminated output."""
    # Look for sentences that don't start with reasoning patterns
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sent in reversed(sentences):
        if not _REASONING_RE.search(sent) and len(sent.strip()) > 10:
            return sent.strip()
    # Last resort: return the last sentence
    if sentences:
        return sentences[-1].strip()
    return text


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

    def _llm_respond(self, user_input: str, agent_name: str) -> tuple[str, str]:
        """
        Generate a response using the LLM with the agent's system prompt.

        Returns:
            Tuple of (clean_response, thinking) where thinking is the raw
            reasoning from <think> tags (empty string if none).
        """
        if self.llm is None:
            intent_map = {
                "info_agent": IntentType.INFORMATION_QUERY,
                "task_agent": IntentType.TASK_MANAGEMENT,
                "chat_agent": IntentType.GENERAL_CHAT,
            }
            return _get_fallback(intent_map.get(agent_name, IntentType.UNKNOWN)), ""

        try:
            # Temporarily set agent-specific system prompt
            original_prompt = self.llm.system_prompt
            self.llm.set_system_prompt(AGENT_PROMPTS.get(agent_name, original_prompt))

            # Append /no_think to suppress Qwen3's internal reasoning mode
            # This produces a cleaner, direct response
            prompt_with_flag = user_input + " /no_think"
            response = self.llm.chat(prompt_with_flag, remember=False)

            # Restore original prompt
            self.llm.set_system_prompt(original_prompt)

            raw = response.content
            thinking = _extract_thinking(raw)
            clean = _strip_think_tags(raw)

            # Detect reasoning leaks (model outputs CoT without <think> tags)
            if _is_reasoning_leak(clean):
                logger.warning("Detected reasoning leak in LLM output, retrying with stricter prompt")
                thinking = clean  # Save the leaked reasoning as thinking
                # Retry with a very explicit instruction
                retry_response = self.llm.chat(
                    user_input + "\n\nIMPORTANT: Reply with ONLY the final answer in 1-2 sentences. "
                    "Do not include any reasoning or thought process.",
                    remember=False,
                )
                retry_raw = retry_response.content
                clean = _strip_think_tags(retry_raw)
                # If retry also leaks, extract just the useful part
                if _is_reasoning_leak(clean):
                    clean = _extract_final_answer(clean)

            # Safety net: if clean response is empty
            if not clean and thinking:
                clean = thinking.split("\n")[0].strip(". ")
                if len(clean) > 200:
                    clean = clean[:197] + "..."

            return clean, thinking

        except Exception as e:
            logger.error(f"LLM generation failed in {agent_name}: {e}")
            intent_map = {
                "info_agent": IntentType.INFORMATION_QUERY,
                "task_agent": IntentType.TASK_MANAGEMENT,
                "chat_agent": IntentType.GENERAL_CHAT,
            }
            return _get_fallback(intent_map.get(agent_name, IntentType.UNKNOWN)), ""

    def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify user intent from input.

        Priority: task > smart_home > info > chat
        Task keywords are checked first so phrases like "set an alarm"
        aren't misrouted to info_agent by matching "what/when/how".
        """
        user_input = state["user_input"].lower()

        # Check task intent FIRST (highest priority after smart home)
        if any(word in user_input for word in [
            "remind", "schedule", "task", "todo", "calendar", "alarm",
            "set a ", "set an ", "timer", "appointment", "meeting",
            "wake me", "wake up", "note", "note down", "add a", "create a",
            "don't forget", "do not forget", "remember to",
            "put a ", "put an ", "keep a ", "keep an ",
            "make a reminder", "make an alarm", "make alarm",
            "o'clock", "oclock", "a.m.", "p.m.",
            "morning alarm", "evening alarm", "night alarm",
        ]):
            intent = IntentType.TASK_MANAGEMENT.value
        elif any(word in user_input for word in [
            "light", "fan", "ac", "door", "temperature", "switch",
            "turn on", "turn off",
        ]):
            intent = IntentType.SMART_HOME.value
        elif any(word in user_input for word in [
            "hello", "hi ", "hey ", "good morning", "good evening",
            "good night", "bye", "thank", "thanks",
        ]):
            intent = IntentType.GENERAL_CHAT.value
        elif any(word in user_input for word in [
            "what", "who", "where", "when", "how", "why", "tell me",
            "explain", "describe", "define", "meaning",
            "latest", "newest", "recent", "best", "top ",
            "movie", "film", "song", "news", "weather",
            "price", "cost", "score", "result",
            "search", "find", "look up", "google", "youtube",
            "list of", "show me", "check out", "any new",
            "video", "recommend", "suggest",
        ]):
            intent = IntentType.INFORMATION_QUERY.value
        else:
            intent = IntentType.GENERAL_CHAT.value

        state["intent"] = intent
        logger.info(f"Classified intent: {intent}")
        return state

    def _route_to_agent(self, state: AgentState) -> str:
        """Route to appropriate agent based on intent."""
        return state.get("intent", IntentType.UNKNOWN.value)

    def _run_info_agent(self, state: AgentState) -> AgentState:
        """Run the information query agent with web search + LLM."""
        logger.info("Running info agent")
        user_input = state["user_input"]

        # Search the web for relevant information
        search_results = self._web_search(user_input)
        sources = []

        if search_results:
            # Build context from search results for the LLM
            context_lines = []
            for i, r in enumerate(search_results[:3], 1):
                context_lines.append(f"[{i}] {r['title']}: {r['body']}")
                sources.append({
                    "title": r["title"],
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })

            context = "\n".join(context_lines)
            augmented_input = (
                f"Answer this question using the search results below.\n\n"
                f"Search results:\n{context}\n\n"
                f"Question: {user_input}"
            )
            response, thinking = self._llm_respond(augmented_input, "info_agent")
        else:
            response, thinking = self._llm_respond(user_input, "info_agent")

        state["agent_outputs"]["info_agent"] = {
            "response": response,
            "thinking": thinking,
            "sources": sources,
            "web_search": len(sources) > 0,
        }
        return state

    @staticmethod
    def _web_search(query: str, max_results: int = 3) -> list:
        """Search the web using DuckDuckGo. Returns list of results or empty list."""
        try:
            from ddgs import DDGS
            results = DDGS().text(query, max_results=max_results)
            logger.info(f"Web search for '{query[:50]}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return []

    def _run_task_agent(self, state: AgentState) -> AgentState:
        """Run the task management agent with LLM and persist the task."""
        logger.info("Running task agent")
        user_input = state["user_input"]

        # Get LLM response first — it often produces a cleaner description
        response, thinking = self._llm_respond(user_input, "task_agent")

        # Extract task title: prefer LLM response, fall back to user input
        task_title = self._extract_task_title_from_response(response)
        if not task_title:
            task_title = self._extract_task_title(user_input)

        # Persist to database
        task_id = None
        try:
            from ..db.database import get_db
            from ..db.models import Task
            db = get_db()
            task = Task(title=task_title, source_input=user_input)
            task_id = db.save_task(task)
            logger.info(f"Task saved: {task_title} (id={task_id})")
        except Exception as e:
            logger.error(f"Failed to save task: {e}")

        state["agent_outputs"]["task_agent"] = {
            "response": response,
            "thinking": thinking,
            "task_created": task_id is not None,
            "task_title": task_title,
        }
        return state

    @staticmethod
    def _extract_task_title_from_response(llm_response: str) -> str:
        """Extract a task title from the LLM's confirmation response.

        E.g. 'Done! Alarm set for 6:00 AM.' -> 'Alarm set for 6:00 AM'
        E.g. 'Done! Remind me to call the doctor.' -> 'Call the doctor'
        """
        if not llm_response:
            return ""
        text = llm_response.strip()
        # Strip common confirmation prefixes
        for prefix in ["done!", "done.", "got it!", "sure!", "okay!", "ok!",
                        "noted!", "saved!", "confirmed!"]:
            if text.lower().startswith(prefix):
                text = text[len(prefix):].strip()
                break
        # Take first sentence only
        for sep in [".", "!", "\n"]:
            if sep in text:
                text = text[:text.index(sep)].strip()
                break
        # Skip if it's a question or too generic
        if not text or len(text) < 5 or "?" in text or text.lower().startswith("let me"):
            return ""
        return text[0].upper() + text[1:]

    @staticmethod
    def _extract_task_title(user_input: str) -> str:
        """Extract a concise task title from user input."""
        text = user_input.strip()
        lower = text.lower()

        # For alarm/wake-up requests, produce "Alarm at <time>"
        alarm_match = re.search(
            r"(?:alarm|wake\s*(?:me\s*)?up)\s*(?:at|for)?\s*(.+)",
            lower,
        )
        if alarm_match:
            time_part = alarm_match.group(1).strip().rstrip(".")
            return f"Alarm at {time_part}"

        # Strip conversational prefixes to get the core task
        for prefix in [
            "please remind me to ", "can you remind me to ",
            "remind me to ", "set a reminder to ",
            "don't let me forget to ", "do not let me forget to ",
            "i need to ", "add a task to ",
            "create a task to ", "create a task ",
            "add task ", "schedule ",
            "remember to ", "note down ",
            "please ",
        ]:
            if lower.startswith(prefix):
                text = text[len(prefix):]
                break

        # Capitalize first letter, limit length
        title = text[0].upper() + text[1:] if text else text
        if len(title) > 120:
            title = title[:117] + "..."
        return title

    def _run_chat_agent(self, state: AgentState) -> AgentState:
        """Run the general chat agent with LLM."""
        logger.info("Running chat agent")
        response, thinking = self._llm_respond(state["user_input"], "chat_agent")

        state["agent_outputs"]["chat_agent"] = {
            "response": response,
            "thinking": thinking,
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

        # Extract sources and thinking from active agent
        active_output = agent_outputs.get(active_agent, {})
        sources = active_output.get("sources", [])
        thinking = active_output.get("thinking", "")

        return {
            "response": result.get("final_response", ""),
            "intent": result.get("intent"),
            "language": result.get("language"),
            "agent": active_agent,
            "sources": sources,
            "thinking": thinking,
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
