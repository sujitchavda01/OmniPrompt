from typing import Dict, Any, List
from jsonschema import validate, Draft202012Validator

SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["meta", "intent", "requirements", "constraints", "deliverables", "confidence"],
    "properties": {
        "meta": {
            "type": "object",
            "required": ["request_id", "timestamp", "sources"],
            "properties": {
                "request_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["type", "path", "extraction_method", "status"],
                        "properties": {
                            "type": {"type": "string"},
                            "path": {"type": "string"},
                            "extraction_method": {"type": "string"},
                            "status": {"type": "string"},
                        },
                    },
                },
            },
        },
        "intent": {"type": "string"},
        "requirements": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "deliverables": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "ambiguities": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}


def validate_refined_prompt(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    validator = Draft202012Validator(SCHEMA)
    for err in sorted(validator.iter_errors(data), key=lambda e: e.path):
        errors.append(f"Validation error at {'/'.join(map(str, err.path))}: {err.message}")
    return errors
