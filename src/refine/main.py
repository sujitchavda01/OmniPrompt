import argparse
import json
from pathlib import Path
from typing import List

from .refine_pipeline import refine
from .validators import validate_refined_prompt


def list_files(folder: Path) -> List[str]:
    paths: List[str] = []
    for p in folder.glob("**/*"):
        if p.is_file():
            paths.append(str(p))
    return paths


def main():
    parser = argparse.ArgumentParser(description="Multi-Modal Prompt Refinement CLI")
    parser.add_argument("--inputs", nargs="*", help="Paths to input files")
    parser.add_argument("--folder", help="Folder of inputs", default=None)
    parser.add_argument("--text", help="Inline text input", default="")
    parser.add_argument("--out", help="Output JSON path", default=None)
    args = parser.parse_args()

    inputs: List[str] = []
    if args.inputs:
        inputs.extend(args.inputs)
    if args.folder:
        inputs.extend(list_files(Path(args.folder)))

    rp, _sources = refine(inputs=inputs, inline_text=args.text)
    data = rp.to_dict()
    errors = validate_refined_prompt(data)

    if errors:
        data["validation_errors"] = errors

    out_json = json.dumps(data, ensure_ascii=False, indent=2)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(out_json, encoding="utf-8")
        print(f"Wrote refined prompt to {args.out}")
    else:
        print(out_json)


if __name__ == "__main__":
    main()
