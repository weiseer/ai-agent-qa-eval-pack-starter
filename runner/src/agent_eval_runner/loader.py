"""Load eval cases from a directory tree of YAML files."""
from __future__ import annotations

import pathlib
from typing import Any

import yaml


def bundled_cases_dir() -> str:
    """Path to the 5 free cases shipped inside the package (zero-config `try`)."""
    return str(pathlib.Path(__file__).parent / "bundled_cases")


def load_cases(cases_dir: str) -> list[dict[str, Any]]:
    """Recursively load every case_*.yaml under cases_dir.

    Returns a list of case dicts sorted by id. Skips the schema file and any
    non-case yaml. Raises if a file is unparseable.
    """
    root = pathlib.Path(cases_dir)
    if not root.exists():
        raise FileNotFoundError(f"cases dir not found: {cases_dir}")
    cases: list[dict[str, Any]] = []
    for p in sorted(root.rglob("*.yaml")):
        if "schema" in p.parts or p.name.startswith("_"):
            continue
        with open(p, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        if not isinstance(doc, dict) or "evaluation" not in doc or "id" not in doc:
            continue  # not a case file
        doc["_path"] = str(p)
        cases.append(doc)
    cases.sort(key=lambda c: c.get("id", ""))
    return cases
