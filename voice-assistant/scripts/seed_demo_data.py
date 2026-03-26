"""
Seed the database with realistic demo conversations for presentation.
Run: python scripts/seed_demo_data.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_db
from src.db.models import Conversation, Message, SystemMetric
import random

DEMO_CONVERSATIONS = [
    # Malayalam queries
    {"lang": "ml", "intent": "information_query", "user": "കേരളത്തിന്റെ തലസ്ഥാനം ഏതാണ്?", "assistant": "കേരളത്തിന്റെ തലസ്ഥാനം തിരുവനന്തപുരം ആണ്.", "asr": 180, "trans": 95, "llm": 420, "tts": 110},
    {"lang": "ml", "intent": "general_chat", "user": "നമസ്കാരം, സുഖമാണോ?", "assistant": "നമസ്കാരം! ഞാൻ നല്ല രീതിയിൽ ആണ്. നിങ്ങൾക്ക് എങ്ങനെ സഹായിക്കാം?", "asr": 150, "trans": 80, "llm": 350, "tts": 120},
    {"lang": "ml", "intent": "task_management", "user": "5 മണിക്ക് അമ്മയെ വിളിക്കാൻ ഓർമ്മിപ്പിക്കൂ", "assistant": "5 മണിക്ക് അമ്മയെ വിളിക്കാനുള്ള ഓർമ്മിപ്പ് സെറ്റ് ചെയ്തിട്ടുണ്ട്.", "asr": 200, "trans": 110, "llm": 380, "tts": 100},
    {"lang": "ml", "intent": "information_query", "user": "ഇന്നത്തെ കാലാവസ്ഥ എന്താണ്?", "assistant": "ഇന്ന് ചൂടുള്ള കാലാവസ്ഥയാണ്, ഏകദേശം 32°C.", "asr": 170, "trans": 90, "llm": 400, "tts": 105},

    # Hindi queries
    {"lang": "hi", "intent": "information_query", "user": "भारत की राजधानी क्या है?", "assistant": "भारत की राजधानी नई दिल्ली है।", "asr": 160, "trans": 85, "llm": 380, "tts": 95},
    {"lang": "hi", "intent": "general_chat", "user": "नमस्ते, कैसे हैं आप?", "assistant": "नमस्ते! मैं अच्छा हूँ। आपकी क्या मदद कर सकता हूँ?", "asr": 140, "trans": 75, "llm": 320, "tts": 90},
    {"lang": "hi", "intent": "task_management", "user": "कल सुबह 8 बजे मीटिंग का रिमाइंडर सेट करो", "assistant": "कल सुबह 8 बजे मीटिंग का रिमाइंडर सेट कर दिया है।", "asr": 190, "trans": 100, "llm": 360, "tts": 100},

    # Tamil queries
    {"lang": "ta", "intent": "information_query", "user": "தமிழ்நாட்டின் தலைநகரம் என்ன?", "assistant": "தமிழ்நாட்டின் தலைநகரம் சென்னை.", "asr": 175, "trans": 92, "llm": 410, "tts": 108},
    {"lang": "ta", "intent": "general_chat", "user": "வணக்கம், எப்படி இருக்கீங்க?", "assistant": "வணக்கம்! நான் நன்றாக இருக்கிறேன். உங்களுக்கு எப்படி உதவ முடியும்?", "asr": 155, "trans": 82, "llm": 340, "tts": 112},

    # Telugu queries
    {"lang": "te", "intent": "information_query", "user": "ఆంధ్ర ప్రదేశ్ రాజధాని ఏది?", "assistant": "ఆంధ్ర ప్రదేశ్ రాజధాని అమరావతి.", "asr": 165, "trans": 88, "llm": 390, "tts": 102},
    {"lang": "te", "intent": "general_chat", "user": "నమస్కారం, ఎలా ఉన్నారు?", "assistant": "నమస్కారం! నేను బాగున్నాను. మీకు ఎలా సహాయం చేయగలను?", "asr": 145, "trans": 78, "llm": 330, "tts": 98},

    # Bengali queries
    {"lang": "bn", "intent": "information_query", "user": "পশ্চিমবঙ্গের রাজধানী কী?", "assistant": "পশ্চিমবঙ্গের রাজধানী কলকাতা।", "asr": 170, "trans": 90, "llm": 400, "tts": 105},

    # English queries
    {"lang": "en", "intent": "information_query", "user": "What is the population of India?", "assistant": "India has a population of approximately 1.4 billion people, making it the most populous country in the world.", "asr": 120, "trans": 0, "llm": 280, "tts": 85},
    {"lang": "en", "intent": "general_chat", "user": "Hello! How are you doing today?", "assistant": "Hello! I'm doing great, thank you for asking. How can I help you today?", "asr": 110, "trans": 0, "llm": 250, "tts": 80},
    {"lang": "en", "intent": "task_management", "user": "Set an alarm for 7 AM tomorrow", "assistant": "I've set an alarm for 7:00 AM tomorrow morning.", "asr": 130, "trans": 0, "llm": 300, "tts": 75},
    {"lang": "en", "intent": "information_query", "user": "What is machine learning?", "assistant": "Machine learning is a subset of artificial intelligence where computer systems learn from data and improve their performance without being explicitly programmed.", "asr": 125, "trans": 0, "llm": 350, "tts": 90},

    # More Malayalam (primary language)
    {"lang": "ml", "intent": "information_query", "user": "ഇന്ത്യയുടെ പ്രധാനമന്ത്രി ആരാണ്?", "assistant": "ഇന്ത്യയുടെ ഇപ്പോഴത്തെ പ്രധാനമന്ത്രി നരേന്ദ്ര മോദി ആണ്.", "asr": 185, "trans": 98, "llm": 430, "tts": 115},
    {"lang": "ml", "intent": "general_chat", "user": "നന്ദി, വളരെ സഹായകരമായിരുന്നു", "assistant": "സ്വാഗതം! എപ്പോഴും സഹായിക്കാൻ ഞാൻ ഇവിടെ ഉണ്ട്.", "asr": 145, "trans": 78, "llm": 310, "tts": 95},
    {"lang": "ml", "intent": "information_query", "user": "സമയം എത്രയായി?", "assistant": "ക്ഷമിക്കണം, ഞാൻ നിലവിലെ സമയം പരിശോധിക്കാൻ കഴിയുന്നില്ല.", "asr": 130, "trans": 72, "llm": 290, "tts": 88},

    # More Hindi
    {"lang": "hi", "intent": "information_query", "user": "मशीन लर्निंग क्या है?", "assistant": "मशीन लर्निंग कृत्रिम बुद्धिमत्ता का एक हिस्सा है जहाँ कंप्यूटर डेटा से सीखते हैं।", "asr": 175, "trans": 95, "llm": 420, "tts": 110},
    {"lang": "hi", "intent": "task_management", "user": "शाम को 6 बजे दवाई लेने का रिमाइंडर", "assistant": "शाम 6 बजे दवाई लेने का रिमाइंडर सेट हो गया।", "asr": 180, "trans": 92, "llm": 340, "tts": 98},
]


def main():
    db = get_db()

    for conv_data in DEMO_CONVERSATIONS:
        total = conv_data["asr"] + conv_data["trans"] + conv_data["llm"] + conv_data["tts"]
        # Add some realistic jitter
        jitter = random.uniform(0.85, 1.15)

        conv = Conversation(
            language=conv_data["lang"],
            intent=conv_data["intent"],
            status="completed",
            asr_time_ms=round(conv_data["asr"] * jitter, 1),
            translation_time_ms=round(conv_data["trans"] * jitter, 1),
            llm_time_ms=round(conv_data["llm"] * jitter, 1),
            tts_time_ms=round(conv_data["tts"] * jitter, 1),
            total_time_ms=round(total * jitter, 1),
        )
        conv.messages = [
            Message(role="user", content=conv_data["user"], language=conv_data["lang"]),
            Message(role="assistant", content=conv_data["assistant"], language=conv_data["lang"]),
        ]
        db.save_conversation(conv)

    count = db.count_conversations()
    print(f"Seeded {len(DEMO_CONVERSATIONS)} conversations. Total in DB: {count}")

    # Show language distribution
    lang_stats = db.get_language_stats()
    print("\nLanguage distribution:")
    for s in lang_stats:
        lang = s.get("language") or s.get("_id", "?")
        print(f"  {lang}: {s.get('count', 0)}")

    intent_stats = db.get_intent_stats()
    print("\nIntent distribution:")
    for s in intent_stats:
        intent = s.get("intent") or s.get("_id", "?")
        print(f"  {intent}: {s.get('count', 0)}")


if __name__ == "__main__":
    main()
