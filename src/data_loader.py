"""Load the static mock data. No database — the brief ships 3 files and that's all
the state this prototype has."""

import json
from functools import lru_cache

from src.config import DATA_DIR


@lru_cache(maxsize=1)
def load_publishers() -> list[dict]:
    with open(DATA_DIR / "publishers.json") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_personas() -> list[dict]:
    with open(DATA_DIR / "shopper_personas.json") as f:
        return json.load(f)


def load_example_advertisers() -> list[str]:
    """Parse the numbered one-liners out of the sample file (skip comments/blanks)."""
    examples: list[str] = []
    with open(DATA_DIR / "example_advertisers.txt") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line == "---":
                continue
            # lines look like "1. We sell premium dog food..."
            if line[0].isdigit() and "." in line:
                examples.append(line.split(".", 1)[1].strip())
    return examples
