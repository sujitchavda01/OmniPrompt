from typing import List, Tuple
from pathlib import Path
import re

from .schema import RefinedPrompt, SourceMeta, make_meta
from .extractor import extract_text_from_string, extract_from_path, detect_type


def _sentences(text: str) -> List[str]:
    # Basic sentence split that respects currency like $5.00
    # Avoid splitting after dots if it looks like a number
    parts = re.split(r"(?<!\d)(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _bullets(text: str) -> List[str]:
    lines = [l.strip(" -•\t") for l in text.splitlines()]
    return [l for l in lines if l]


def _collect_requirements(sentences: List[str]) -> List[str]:
    # Heuristic: sentences with modal verbs or leading bullets
    req_markers = ["must", "should", "need to", "required", "support", "allow", "enable"]
    results: List[str] = []
    for s in sentences:
        s_l = s.lower()
        if any(m in s_l for m in req_markers):
            results.append(s)
    return results


def _collect_constraints(sentences: List[str]) -> List[str]:
    markers = ["constraint", "limited", "deadline", "budget", "tech stack", "only", "at most", "no ", "cannot", "$", "usd", "cost"]
    results: List[str] = []
    for s in sentences:
        s_l = s.lower()
        if any(m in s_l for m in markers):
            # Check for currency symbols or numbers related to budget
            if "$" in s or "budget" in s_l:
                results.append(s)
            elif any(m in s_l for m in markers):
                results.append(s)
    # Deduplicate
    return list(dict.fromkeys(results))


def _collect_deliverables(sentences: List[str]) -> List[str]:
    markers = ["deliver", "output", "artifact", "report", "document", "prototype", "mockup", "api spec"]
    results: List[str] = []
    for s in sentences:
        s_l = s.lower()
        if any(m in s_l for m in markers):
            results.append(s)
    return results


def _guess_intent(text: str) -> str:
    sents = _sentences(text)
    if not sents:
        return text.strip()[:240]
    # Prefer sentences with verbs like build/design/create
    intent_markers = ["build", "design", "create", "develop", "make"]
    for s in sents[:5]:
        if any(m in s.lower() for m in intent_markers):
            return s
    return sents[0]


def _find_ambiguities(text: str) -> List[str]:
    patterns = [
        (r"TBD|to be decided", "Unspecified details (TBD) present"),
        (r"\b(?:\d+)\s*(?:days|weeks|months)?\b", "Numeric values might be constraints; verify"),
        (r"\b(?:etc\.|and so on)\b", "Ambiguous lists (etc.)"),
    ]
    flags: List[str] = []
    for pat, msg in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            flags.append(msg)
    return list(dict.fromkeys(flags))


def refine(inputs: List[str], inline_text: str = "") -> Tuple[RefinedPrompt, List[SourceMeta]]:
    corpus_parts: List[str] = []
    sources: List[SourceMeta] = []

    if inline_text.strip():
        text, meta = extract_text_from_string(inline_text)
        corpus_parts.append(text)
        sources.append(SourceMeta(type="text", path="<inline>", extraction_method=meta["extraction_method"], status=meta["status"]))

    for inp in inputs:
        p = Path(inp)
        t = detect_type(p)
        text, meta = extract_from_path(p)
        corpus_parts.append(text)
        sources.append(SourceMeta(type=t, path=str(p), extraction_method=meta.get("extraction_method", "unknown"), status=meta.get("status", "unknown")))

    corpus = "\n\n".join([c for c in corpus_parts if c])
    sents = _sentences(corpus)

    requirements = _collect_requirements(sents)
    constraints = _collect_constraints(sents)
    deliverables = _collect_deliverables(sents)

    intent = _guess_intent(corpus)
    ambiguities = _find_ambiguities(corpus)

    assumptions: List[str] = []
    open_questions: List[str] = []

    # Simple inference rules
    if not deliverables:
        open_questions.append("What are the expected deliverables/artifacts?")
    if not constraints:
        assumptions.append("No strict technical constraints provided; flexibility assumed.")
    if not requirements:
        open_questions.append("What are the core functional requirements?")

    # Confidence heuristic
    coverage = sum(bool(x) for x in [intent, requirements, constraints, deliverables])
    confidence = 0.3 + 0.15 * coverage
    confidence = max(0.0, min(1.0, confidence))

    rp = RefinedPrompt(
        meta=make_meta(sources),
        intent=intent,
        requirements=requirements,
        constraints=constraints,
        deliverables=deliverables,
        assumptions=assumptions,
        ambiguities=ambiguities,
        open_questions=open_questions,
        confidence=confidence,
    )

    return rp, sources
