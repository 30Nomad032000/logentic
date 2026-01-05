"""
Intent Detection Module
Detects user intent from transcribed text.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents."""
    GREETING = "greeting"
    QUESTION = "question"
    COMMAND = "command"
    INFORMATION = "information"
    TASK = "task"
    WEATHER = "weather"
    TIME = "time"
    REMINDER = "reminder"
    CALCULATION = "calculation"
    TRANSLATION = "translation"
    GENERAL = "general"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Detected intent with metadata."""
    type: IntentType
    confidence: float
    entities: dict
    original_text: str
    english_text: str
    description: str


class IntentDetector:
    """
    Detects intent from user input.
    Uses keyword matching + LLM for complex cases.
    """

    # Keyword patterns for quick intent detection
    INTENT_PATTERNS = {
        IntentType.GREETING: [
            "hello", "hi", "hey", "good morning", "good evening",
            "namaste", "how are you", "what's up"
        ],
        IntentType.WEATHER: [
            "weather", "temperature", "rain", "sunny", "cloudy",
            "forecast", "climate", "hot", "cold"
        ],
        IntentType.TIME: [
            "time", "what time", "clock", "hour", "date", "today",
            "day", "month", "year"
        ],
        IntentType.REMINDER: [
            "remind", "reminder", "alarm", "schedule", "appointment",
            "notify", "alert", "set reminder"
        ],
        IntentType.CALCULATION: [
            "calculate", "math", "plus", "minus", "multiply", "divide",
            "sum", "total", "percentage", "how much is"
        ],
        IntentType.QUESTION: [
            "what", "who", "where", "when", "why", "how", "which",
            "is it", "are you", "can you", "could you", "tell me"
        ],
        IntentType.COMMAND: [
            "turn on", "turn off", "switch", "open", "close",
            "start", "stop", "play", "pause", "set"
        ],
    }

    def __init__(self, use_llm: bool = True):
        """
        Initialize intent detector.

        Args:
            use_llm: Whether to use LLM for complex intent detection
        """
        self.use_llm = use_llm
        self._llm = None

    def _get_llm(self):
        """Lazy load LLM for intent detection."""
        if self._llm is None and self.use_llm:
            from ..llm import QwenLLM
            self._llm = QwenLLM(model_size="1.5b")
            # Set a specific system prompt for intent detection
            self._llm.set_system_prompt("""You are an intent classifier. Given a user message, identify:
1. The primary intent (greeting, question, command, weather, time, reminder, calculation, information, task, general)
2. Key entities mentioned (names, numbers, locations, times)
3. A brief description of what the user wants

Respond in this exact format:
INTENT: <intent_type>
ENTITIES: <key: value pairs or "none">
DESCRIPTION: <brief description>""")
        return self._llm

    def detect(
        self,
        text: str,
        english_text: Optional[str] = None,
    ) -> Intent:
        """
        Detect intent from text.

        Args:
            text: Original text (Malayalam or English)
            english_text: English translation (if available)

        Returns:
            Intent object with detected intent
        """
        # Use English text for detection if available
        analysis_text = english_text.lower() if english_text else text.lower()

        logger.info(f"Detecting intent for: '{analysis_text[:50]}...'")

        # Try keyword-based detection first
        detected_intent = self._keyword_detect(analysis_text)

        if detected_intent and detected_intent != IntentType.UNKNOWN:
            return Intent(
                type=detected_intent,
                confidence=0.8,
                entities={},
                original_text=text,
                english_text=english_text or text,
                description=self._get_intent_description(detected_intent, analysis_text)
            )

        # Use LLM for complex cases
        if self.use_llm:
            return self._llm_detect(text, english_text or text)

        # Default to general intent
        return Intent(
            type=IntentType.GENERAL,
            confidence=0.5,
            entities={},
            original_text=text,
            english_text=english_text or text,
            description="General conversation or query"
        )

    def _keyword_detect(self, text: str) -> Optional[IntentType]:
        """Detect intent using keyword matching."""
        text_lower = text.lower()

        # Check each intent pattern
        scores = {}
        for intent_type, keywords in self.INTENT_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[intent_type] = score

        if scores:
            # Return intent with highest score
            return max(scores, key=scores.get)

        return None

    def _llm_detect(self, original_text: str, english_text: str) -> Intent:
        """Use LLM for intent detection."""
        llm = self._get_llm()

        if llm is None:
            return Intent(
                type=IntentType.GENERAL,
                confidence=0.5,
                entities={},
                original_text=original_text,
                english_text=english_text,
                description="General query"
            )

        try:
            response = llm.chat(
                f"Classify this user message: \"{english_text}\"",
                remember=False,
                max_new_tokens=100,
            )

            # Parse LLM response
            return self._parse_llm_response(
                response.content,
                original_text,
                english_text
            )

        except Exception as e:
            logger.error(f"LLM intent detection failed: {e}")
            return Intent(
                type=IntentType.GENERAL,
                confidence=0.5,
                entities={},
                original_text=original_text,
                english_text=english_text,
                description="General query"
            )

    def _parse_llm_response(
        self,
        response: str,
        original_text: str,
        english_text: str
    ) -> Intent:
        """Parse LLM response into Intent object."""
        intent_type = IntentType.GENERAL
        entities = {}
        description = "General query"

        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("INTENT:"):
                intent_str = line.replace("INTENT:", "").strip().lower()
                try:
                    intent_type = IntentType(intent_str)
                except ValueError:
                    intent_type = IntentType.GENERAL
            elif line.startswith("ENTITIES:"):
                entities_str = line.replace("ENTITIES:", "").strip()
                if entities_str.lower() != "none":
                    # Simple parsing of key: value pairs
                    for pair in entities_str.split(","):
                        if ":" in pair:
                            k, v = pair.split(":", 1)
                            entities[k.strip()] = v.strip()
            elif line.startswith("DESCRIPTION:"):
                description = line.replace("DESCRIPTION:", "").strip()

        return Intent(
            type=intent_type,
            confidence=0.85,
            entities=entities,
            original_text=original_text,
            english_text=english_text,
            description=description
        )

    def _get_intent_description(self, intent_type: IntentType, text: str) -> str:
        """Generate description for keyword-detected intent."""
        descriptions = {
            IntentType.GREETING: "User is greeting or starting a conversation",
            IntentType.WEATHER: "User is asking about weather or climate",
            IntentType.TIME: "User is asking about time or date",
            IntentType.REMINDER: "User wants to set a reminder or alarm",
            IntentType.CALCULATION: "User wants to perform a calculation",
            IntentType.QUESTION: "User is asking a question",
            IntentType.COMMAND: "User is giving a command or instruction",
            IntentType.GENERAL: "General conversation or query",
        }
        return descriptions.get(intent_type, "General query")
