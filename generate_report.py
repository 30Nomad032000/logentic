"""
Generate project report by cloning the reference document and replacing content.
Preserves all formatting, images, borders, and styles from the original.
"""
from docx import Document

SOURCE = r"C:\Users\Admin\Downloads\project 1 (1).docx"
OUTPUT = r"D:\Work\logentic\Project_Report_Voice_Assistant.docx"

NEW_TITLE_MIXED = "Hyper-Localized Multilingual Voice Assistant Using Edge Computing and Agentic Workflows"


def replace_in_paragraph(paragraph, old_text, new_text):
    """Replace text in a paragraph, keeping first run's formatting."""
    full_text = paragraph.text
    if old_text not in full_text:
        return False
    new_full = full_text.replace(old_text, new_text)
    if not paragraph.runs:
        return False
    paragraph.runs[0].text = new_full
    for run in paragraph.runs[1:]:
        run.text = ""
    return True


def main():
    doc = Document(SOURCE)
    done = []

    for para in doc.paragraphs:
        t = para.text

        # ── TITLE (all caps, appears on cover pages) ──
        if "AUTOMATIC TEXT SUMMARIZATION USING NLP" in t:
            replace_in_paragraph(para, t, t.replace(
                "AUTOMATIC TEXT SUMMARIZATION USING NLP",
                "HYPER-LOCALIZED MULTILINGUAL VOICE ASSISTANT USING EDGE COMPUTING AND AGENTIC WORKFLOWS"
            ))
            done.append("TITLE")
            continue

        # ── DECLARATION (must come before generic NAME/REG replacements) ──
        if "I hereby declare" in t:
            new = t.replace(
                "Automatic Text Summarization using Natural Language Processing",
                NEW_TITLE_MIXED
            ).replace(
                "Ms. Rintu Augustine Assistant professor",
                "Prof. Sukrith Lal Assistant Professor"
            ).replace("ALEXANDER SAJAN", "EBIN JOHN JOSEPH"
            ).replace("ASI24MCA-2006", "ASI24MCA-2025")
            replace_in_paragraph(para, t, new)
            done.append("DECLARATION")
            continue

        # ── CERTIFICATE (must come before generic NAME/REG replacements) ──
        if "This is to certify" in t:
            new = t
            # Replace title (handle various quote characters)
            new = new.replace(
                "Automatic Text Summarization using Natural Language Processing",
                NEW_TITLE_MIXED
            )
            new = new.replace("ALEXANDER SAJAN", "EBIN JOHN JOSEPH")
            new = new.replace("ASI24MCA-2006", "ASI24MCA-2025")
            new = new.replace("him/her", "him")
            replace_in_paragraph(para, t, new)
            done.append("CERTIFICATE")
            continue

        # ── STUDENT NAME ──
        if "ALEXANDER SAJAN" in t:
            replace_in_paragraph(para, t, t.replace("ALEXANDER SAJAN", "EBIN JOHN JOSEPH"))
            done.append("NAME")
            continue

        # ── REG NUMBER ──
        if "ASI24MCA-2006" in t:
            replace_in_paragraph(para, t, t.replace("ASI24MCA-2006", "ASI24MCA-2025"))
            done.append("REG")
            continue

        # ── GUIDE NAME (heading style, cover page 2) ──
        if t.strip() == "Ms. Rintu Augustine":
            replace_in_paragraph(para, t, t.replace("Ms. Rintu Augustine", "Prof. Sukrith Lal"))
            done.append("GUIDE_COVER")
            continue

        # ── GUIDE TITLE ──
        if t.strip() == "Assistant professor":
            replace_in_paragraph(para, t, t.replace("Assistant professor", "Assistant Professor"))
            done.append("GUIDE_TITLE")
            continue

        # (Declaration and Certificate handled above, before NAME/REG)

        # ── CERTIFICATE: Guide + HOD line ──
        if "Asst. Prof. Rintu Augustine" in t and "Dr." in t:
            replace_in_paragraph(para, t, t.replace(
                "Asst. Prof. Rintu Augustine", "Prof. Sukrith Lal"
            ))
            done.append("CERT_GUIDE_LINE")
            continue

        # ── ACKNOWLEDGEMENT: Guide paragraph ──
        if "Asst. Prof. Rintu Augustine" in t or ("Rintu Augustine" in t and "heartfelt" in t):
            new = t.replace("Asst. Prof. Rintu Augustine", "Prof. Sukrith Lal")
            new = new.replace("Rintu Augustine", "Sukrith Lal")
            new = new.replace("Her insights", "His insights")
            new = new.replace("Her ", "His ")
            new = new.replace("her ", "his ")
            new = new.replace(
                "automatic text summarization using Natural Language Processing",
                "building a hyper-localized multilingual voice assistant using edge computing and agentic workflows"
            )
            replace_in_paragraph(para, t, new)
            done.append("ACK_GUIDE")
            continue

        # ── ACKNOWLEDGEMENT: College paragraph ──
        if "full-stack web application development" in t:
            new = t.replace(
                "full-stack web application development",
                "advanced machine learning, natural language processing, and edge computing"
            ).replace(
                "software engineering and modern AI-based systems",
                "AI-driven software engineering and modern voice-based systems"
            )
            replace_in_paragraph(para, t, new)
            done.append("ACK_COLLEGE")
            continue

        # ── ACKNOWLEDGEMENT: Open source paragraph ──
        if "modern frameworks and NLP libraries" in t:
            new = t.replace(
                "modern frameworks and NLP libraries",
                "modern frameworks such as PyTorch, Transformers, LangGraph, and FastAPI"
            )
            replace_in_paragraph(para, t, new)
            done.append("ACK_OPEN")
            continue

        # ── ACKNOWLEDGEMENT: Feedback paragraph ──
        if "testing phase" in t and "real-world user requirements" in t and "languages" not in t:
            new = t.replace(
                "real-world user requirements.",
                "real-world user requirements across multiple Indian languages."
            )
            if new != t:
                replace_in_paragraph(para, t, new)
                done.append("ACK_FEEDBACK")
            continue

        # ── ABSTRACT paragraph 1 ──
        if "intelligent system" in t and "Automatic Text Summarization" in t:
            new = t.replace(
                "\u201cAutomatic Text Summarization using Natural Language Processing (NLP)\u201d, "
                "designed to efficiently process and condense large volumes of textual data into "
                "concise and meaningful summaries. The primary problem addressed is the difficulty "
                "faced by users in understanding and analyzing lengthy documents, which is "
                "time-consuming and often impractical in today\u2019s information-rich environment.",

                "\u201cHyper-Localized Multilingual Voice Assistant Using Edge Computing and "
                "Agentic Workflows\u201d, designed to enable seamless interaction with digital "
                "services through natural voice commands in regional Indian languages. The primary "
                "problem addressed is the digital divide faced by millions of users in India who "
                "are unable to effectively interact with technology due to limited support for their "
                "native languages, particularly in voice-based interfaces."
            )
            replace_in_paragraph(para, t, new)
            done.append("ABSTRACT_1")
            continue

        # ── ABSTRACT paragraph 2 ──
        if "reduce reading time" in t or "TF-IDF" in t:
            new = (
                "The system\u2019s core objective is to bridge this accessibility gap by providing a "
                "voice assistant that supports 11 Indian languages including Malayalam, Hindi, Tamil, "
                "Telugu, Bengali, Marathi, Gujarati, Kannada, Punjabi, Urdu, and English. The solution "
                "integrates a complete processing pipeline comprising Automatic Speech Recognition (ASR) "
                "using the Pingala V1 model, bidirectional translation using IndicTrans2, intent detection "
                "using keyword-based and ML-based classifiers, response generation using locally-deployed "
                "Qwen3 large language models, and Text-to-Speech (TTS) synthesis using Meta MMS-TTS."
            )
            replace_in_paragraph(para, t, new)
            done.append("ABSTRACT_2")
            continue

        # ── ABSTRACT paragraph 3 ──
        if "user input handling" in t or "PDF or Word files" in t:
            new = (
                "The system is structured using a modular architecture with LangGraph-based agentic "
                "workflows that intelligently route user queries to specialized agents\u2014including "
                "Information, Task Management, Conversation, and Smart Home agents\u2014enabling "
                "context-aware and domain-specific responses. The entire system is designed for edge "
                "deployment on Raspberry Pi 5 hardware, utilizing quantized models and CPU-first "
                "inference strategies to achieve low-latency, privacy-preserving, and offline-capable "
                "operation. A FastAPI-based REST and WebSocket API serves as the backend, complemented "
                "by a React-based monitoring dashboard for real-time system analytics."
            )
            replace_in_paragraph(para, t, new)
            done.append("ABSTRACT_3")
            continue

    doc.save(OUTPUT)
    print(f"Saved: {OUTPUT}")
    print(f"Replacements: {len(done)}")
    for d in done:
        print(f"  {d}")


if __name__ == "__main__":
    main()
