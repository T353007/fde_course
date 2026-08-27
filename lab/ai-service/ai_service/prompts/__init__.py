"""Prompt templates, versioned by filename.

The version is in the filename and it is part of the fixture key, so bumping a
prompt is a real event. You cannot quietly edit txn_classify_v3.txt and keep the
old eval numbers, because the recorded fixtures are keyed on the version.

That is deliberate. Prompt changes are code changes.

Templates use $name placeholders instead of {name}, because most of these
templates contain JSON examples full of braces.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).resolve().parent


class PromptNotFound(FileNotFoundError):
    pass


@lru_cache
def load_prompt(version: str) -> str:
    """Read a prompt template by version name, with or without the extension."""
    name = version if version.endswith(".txt") else f"{version}.txt"
    path = PROMPT_DIR / name
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in PROMPT_DIR.glob("*.txt")))
        raise PromptNotFound(
            f"No prompt template named {version!r}. Available: {available}."
        )
    return path.read_text(encoding="utf-8")


def render(version: str, **values: object) -> str:
    """Fill a template. Missing placeholders raise instead of passing silently."""
    template = Template(load_prompt(version))
    return template.substitute(**values)


def available_versions() -> list[str]:
    return sorted(p.stem for p in PROMPT_DIR.glob("*.txt"))
