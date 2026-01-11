from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
import uuid
from datetime import datetime


@dataclass
class SourceMeta:
    type: str
    path: str
    extraction_method: str
    status: str


@dataclass
class RefinedPrompt:
    meta: Dict[str, Any]
    intent: str
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def make_meta(sources: List[SourceMeta]) -> Dict[str, Any]:
    return {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sources": [asdict(s) for s in sources],
    }
