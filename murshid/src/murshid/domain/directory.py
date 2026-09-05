"""The service directory: the only trusted source of service facts.

Rendered into the FAQ prompt's *stable prefix* (Module 6 §3 — byte-stable, so the
provider caches it), delimited as trusted content, and used by Module 5's
groundedness rubric as the ground truth an answer is graded against.

Rendering is deliberately deterministic: the same directory renders byte-identical
every time. A rendering that sorted a dict or stamped a date would quietly destroy
the prompt cache — which is precisely the bug Lab 6 task 2 hunts.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DIRECTORY_PATH = PROJECT_ROOT / "data" / "service_directory.yaml"

Language = Literal["ar", "en"]


class Bilingual(BaseModel):
    en: str = ""
    ar: str = ""

    def get(self, language: str) -> str:
        return self.ar if language == "ar" else self.en


class BilingualList(BaseModel):
    en: list[str] = Field(default_factory=list)
    ar: list[str] = Field(default_factory=list)

    def get(self, language: str) -> list[str]:
        return self.ar if language == "ar" else self.en


class ServiceEntry(BaseModel):
    id: str
    service_type: str
    title: Bilingual
    keywords: BilingualList
    fee: Bilingual
    processing_time: Bilingual
    documents: BilingualList
    steps: BilingualList

    def all_keywords(self) -> list[str]:
        return [k.lower() for k in self.keywords.en] + list(self.keywords.ar)


class ServiceDirectory(BaseModel):
    version: str
    service_centre: Bilingual
    entries: list[ServiceEntry]

    def by_id(self, entry_id: str) -> ServiceEntry | None:
        return next((e for e in self.entries if e.id == entry_id), None)

    def render(self, language: Language = "en") -> str:
        """Markdown, stable byte-for-byte for a given directory version+language."""
        lines = [f"Directory version: {self.version}", ""]
        for e in self.entries:
            lines.append(f"### {e.id} — {e.title.get(language)}")
            lines.append(f"- service_type: {e.service_type}")
            lines.append(f"- fee: {e.fee.get(language)}")
            lines.append(f"- processing_time: {e.processing_time.get(language)}")
            lines.append("- documents: " + "; ".join(e.documents.get(language)))
            lines.append("- steps: " + " | ".join(e.steps.get(language)))
            lines.append("- keywords: " + ", ".join(e.keywords.get(language)))
            lines.append("")
        lines.append(f"service_centre: {self.service_centre.get(language)}")
        return "\n".join(lines)


@lru_cache(maxsize=4)
def load_directory(path: str | Path | None = None) -> ServiceDirectory:
    raw = yaml.safe_load(Path(path or DIRECTORY_PATH).read_text(encoding="utf-8"))
    return ServiceDirectory(**raw)


@lru_cache(maxsize=8)
def rendered_directory(language: Language = "en") -> str:
    return load_directory().render(language)
