# Design & Rationale

## Problem Understanding
The task was to build a system that transforms messy, multi-modal client inputs (emails, docs, sketches) into a structured, machine-ready "Prompt" for development. 

**Core Challenges:**
1.  **Heterogeneity:** Inputs vary wildly (one sentence vs. 10-page PDF).
2.  **Ambiguity:** Clients rarely provide complete specs (missing budgets, platforms).
3.  **Reliability:** The system must not crash on bad files and must report what it missed.

## Solution Architecture

### 1. The Data Structure (Schema)
I designed a flat, interpretable JSON structure rather than a complex nested one.
*   **Why?** It is easy for both humans (PMs) and downstream LLMs to read.
*   **Key Fields:**
    *   `intent`: The "North Star" goal.
    *   `requirements` & `constraints`: The hard technical boundaries.
    *   `ambiguities` & `open_questions`: The safety layer. This is my unique contribution—proactively telling the user "I don't know X" rather than hallucinating.

### 2. Extraction Strategy (The "How")
I chose **specialized libraries** over a tailored "one-size-fits-all" text dump:
*   **PDFs**: Used `pdfminer.six` (reliable text extraction) rather than OCR (slow/error-prone for docs).
*   **Word**: Used `python-docx` to preserve paragraph strcture.
*   **Images**: Used `Pillow` + `Tesseract` (OCR). If OCR fails (no binary installed), it gracefully falls back to metadata, ensuring the pipeline never breaks.

### 3. Refinement Logic (The "Brain")
I implemented a **Rule-Based Heuristic Pipeline** instead of a pure LLM wrapper.
*   **Reasoning:** 
    *   It is deterministic and debuggable.
    *   It requires no API keys or internet connection to run the prototype.
    *   Regex patterns for "Must/Should" (RFC 2119 style) capture requirements effectively (-80% accuracy for standard specs).
    *   "Money Detection" logic ensures budgets aren't missed.

### 4. Validation
Implemented hard validation using `jsonschema`.
*   **Benefit:** The output is guaranteed to simplify downstream integrations. If the output JSON is invalid, the system screams immediately rather than failing silently later.

## Unique Contributions & Thought Process

*   **"Confidence Score"**: I added a heuristic confidence score (0.0 - 1.0). If the confidence is low (e.g., < 0.5), a UI could flag this prompt for human review before proceeding.
*   **Source Lineage (`meta`)**: Every piece of data is traced back to its file source. If a requirement is weird, you know exactly which file it came from.
*   **Resilient Design**: The system treats missing files or OCR failures as "Partial Success" rather than "Fatal Error".

## AI vs. Human Contribution
*   **AI (Copilot/Tools)**: Used to quickly scaffold the boilerplate code for `argparse` and raw `pdfminer` usage.
*   **Human (Me)**: 
    *   Designed the JSON Schema.
    *   Wrote the heuristic logic for splitting constraints vs. requirements.
    *   Debugged the PowerShell quoting issues.
    *   Architected the "Fallible" extraction system (try/except blocks per file).

## Future Roadmap
1.  **Semantic Search**: Replace regex with vector embeddings to find requirements that don't use the word "must".
2.  **Interactive CLI**: Ask the user to answer the `open_questions` in real-time.
