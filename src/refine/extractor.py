from typing import Tuple, Dict, Any, List
from pathlib import Path

from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
from PIL import Image

try:
    import pytesseract  # type: ignore
except Exception:
    pytesseract = None  # OCR optional


def _norm_lines(text: str) -> List[str]:
    lines = [l.strip() for l in text.splitlines()]
    return [l for l in lines if l]


def extract_text_from_string(s: str) -> Tuple[str, Dict[str, Any]]:
    return s, {"extraction_method": "raw_text", "status": "ok"}


def extract_text_from_pdf(path: Path) -> Tuple[str, Dict[str, Any]]:
    try:
        text = pdf_extract_text(str(path))
        status = "ok" if text and text.strip() else "partial"
        return text or "", {"extraction_method": "pdfminer", "status": status}
    except Exception as e:
        return "", {"extraction_method": "pdfminer", "status": f"error: {e}"}


def extract_text_from_docx(path: Path) -> Tuple[str, Dict[str, Any]]:
    try:
        doc = Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs)
        status = "ok" if text and text.strip() else "partial"
        return text or "", {"extraction_method": "python-docx", "status": status}
    except Exception as e:
        return "", {"extraction_method": "python-docx", "status": f"error: {e}"}


def extract_info_from_image(path: Path) -> Tuple[str, Dict[str, Any]]:
    method = "PIL" if pytesseract is None else "pytesseract"
    try:
        img = Image.open(str(path))
        meta = {
            "extraction_method": method,
            "status": "ok",
            "format": img.format,
            "size": img.size,
            "mode": img.mode,
        }
        text = ""
        if pytesseract is not None:
            try:
                # Allow TESSERACT_PATH env override
                # On Windows, pytesseract will use installed tesseract if available
                text = pytesseract.image_to_string(img)
                meta["status"] = "ok" if text.strip() else "partial"
            except Exception as e:
                meta["status"] = f"error: {e}"
        return text or "", meta
    except Exception as e:
        return "", {"extraction_method": method, "status": f"error: {e}"}


def detect_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".pdf"}:
        return "pdf"
    if ext in {".docx"}:
        return "docx"
    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}:
        return "image"
    return "text"


def extract_from_path(path: Path) -> Tuple[str, Dict[str, Any]]:
    if not path.exists():
        return "", {"extraction_method": "none", "status": f"error: File not found: {path}"}
    
    t = detect_type(path)
    if t == "pdf":
        return extract_text_from_pdf(path)
    if t == "docx":
        return extract_text_from_docx(path)
    if t == "image":
        text, meta = extract_info_from_image(path)
        if not text.strip():
            # Fall back to filename as weak hint
            text = path.stem.replace("_", " ")
        return text, meta
    # default: treat as text
    try:
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
        return content, {"extraction_method": "file-text", "status": "ok"}
    except Exception as e:
        return "", {"extraction_method": "file-text", "status": f"error: {e}"}
