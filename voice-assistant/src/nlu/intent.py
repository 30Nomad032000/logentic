"""
Intent Classification Module
Classifies user intent and extracts entities from natural language input.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Result of intent classification."""
    intent: str
    confidence: float
    entities: List[Dict[str, Any]]
    language: str


class IntentClassifier:
    """
    Intent classifier for multilingual voice assistant.

    Supports classification in multiple Indian languages.
    """

    INTENTS = {
        "greeting": ["hello", "hi", "namaste", "vanakkam", "namaskar"],
        "farewell": ["bye", "goodbye", "see you", "alvida"],
        "weather": ["weather", "temperature", "rain", "mausam"],
        "time": ["time", "samay", "clock", "what time"],
        "reminder": ["remind", "reminder", "yaad dilao", "schedule"],
        "search": ["search", "find", "look for", "dhundho"],
        "play_music": ["play", "music", "song", "gaana"],
        "smart_home": ["light", "fan", "ac", "door", "turn on", "turn off"],
        "help": ["help", "madad", "assist", "sahayata"],
    }

    def __init__(self, model_type: str = "keyword"):
        """
        Initialize intent classifier.

        Args:
            model_type: Type of classifier - 'keyword', 'ml', or 'llm'
        """
        self.model_type = model_type
        self.model = None

    def classify(
        self,
        text: str,
        language: str = "en",
    ) -> IntentResult:
        """
        Classify intent from text input.

        Args:
            text: User input text
            language: Language code

        Returns:
            IntentResult with intent, confidence, and entities
        """
        text_lower = text.lower()

        if self.model_type == "keyword":
            return self._keyword_classify(text_lower, language)
        elif self.model_type == "ml":
            return self._ml_classify(text, language)
        else:
            return self._llm_classify(text, language)

    def _keyword_classify(self, text: str, language: str) -> IntentResult:
        """Simple keyword-based classification."""
        best_intent = "unknown"
        best_confidence = 0.0

        for intent, keywords in self.INTENTS.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                confidence = min(matches / len(keywords) + 0.3, 1.0)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent

        # Extract basic entities
        entities = self._extract_entities(text)

        return IntentResult(
            intent=best_intent,
            confidence=best_confidence,
            entities=entities,
            language=language,
        )

    def _ml_classify(self, text: str, language: str) -> IntentResult:
        """ML-based classification (placeholder)."""
        # TODO: Implement with trained classifier
        logger.info("ML classification not yet implemented, using keyword fallback")
        return self._keyword_classify(text.lower(), language)

    def _llm_classify(self, text: str, language: str) -> IntentResult:
        """LLM-based classification (placeholder)."""
        # TODO: Implement with LLM API
        logger.info("LLM classification not yet implemented, using keyword fallback")
        return self._keyword_classify(text.lower(), language)

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text (basic implementation)."""
        entities = []

        # Simple time extraction
        import re
        time_pattern = r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\b'
        times = re.findall(time_pattern, text)
        for t in times:
            entities.append({"type": "time", "value": t})

        # Simple number extraction
        number_pattern = r'\b(\d+)\b'
        numbers = re.findall(number_pattern, text)
        for n in numbers:
            if n not in [e["value"] for e in entities]:
                entities.append({"type": "number", "value": n})

        return entities

    def get_supported_intents(self) -> List[str]:
        """Return list of supported intents."""
        return list(self.INTENTS.keys())
