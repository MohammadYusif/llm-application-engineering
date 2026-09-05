"""Murshid's three tools — one per risk class, deliberately.

Tool schemas are prompts wearing a type system. The model chooses tools by reading
names and descriptions, so both are written for the model and tested like prompts:

* **names** are verb_noun and unambiguous. One registry containing both
  ``check_status`` and ``get_status`` guarantees misrouting;
* **descriptions** say when to use the tool, when *not* to, and what it returns.
  A description that describes the API ("wrapper around the ODS v2 endpoint")
  cannot route anything. The ``sim-greedy-tools`` branch is a description that
  says "use for any question about applications", and it fires on everything;
* **parameters** prefer enums to free strings wherever the domain is closed, and
  document formats in the description.

The risk class is *in code*, reviewable at a glance, because the authorisation
gate keys off it and a gate that depends on someone remembering is not a gate.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, ConfigDict

from murshid.tools.services import booking_service, escalation_service, status_lookup

RiskClass = Literal["read_only", "side_effecting", "terminal"]


class Tool(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    parameters: dict  # JSON Schema
    risk: RiskClass
    fn: Callable  # executed by the APPLICATION, never by the model

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


CITY_ENUM = ["Riyadh", "Jeddah", "Makkah", "Dammam", "Madinah", "Abha", "Tabuk", "Buraidah"]

TOOLS: list[Tool] = [
    Tool(
        name="check_application_status",
        risk="read_only",
        description=(
            "Look up the current status of a government application by its reference "
            "number (format: two letters followed by eight digits, e.g. CR12345678). "
            "Use when the citizen asks about an application they have already "
            "submitted. Do NOT use for starting a new application, and do NOT use "
            "when the citizen has not given a reference number — ask for it instead. "
            "Returns the status, the date it was last updated, and any case note."
        ),
        parameters={
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "pattern": "^[A-Z]{2}[0-9]{8}$",
                    "description": "The application reference, e.g. CR12345678",
                }
            },
            "required": ["reference"],
            "additionalProperties": False,
        },
        fn=status_lookup,
    ),
    Tool(
        name="book_appointment",
        risk="side_effecting",
        description=(
            "Book a service-centre appointment for the AUTHENTICATED citizen. Use "
            "only after the citizen has explicitly confirmed the service, the city "
            "and a specific future working day. Do NOT use to check availability, "
            "and do NOT use to book on behalf of anyone else — the portal will "
            "refuse it. Returns the confirmation number."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service_type": {
                    "type": "string",
                    "enum": [
                        "commercial_licence",
                        "civil_records",
                        "traffic_services",
                        "municipal_permits",
                    ],
                },
                "city": {"type": "string", "enum": CITY_ENUM},
                "date": {
                    "type": "string",
                    "description": "YYYY-MM-DD. Must be a future working day (Sunday to Thursday).",
                },
            },
            "required": ["service_type", "city", "date"],
            "additionalProperties": False,
        },
        fn=booking_service.book,
    ),
    Tool(
        name="escalate_to_agent",
        risk="terminal",
        description=(
            "Transfer the conversation to a human agent. Use when the citizen asks "
            "for a person, is distressed, is making a complaint that needs a human "
            "decision, or the request is outside what self-service can do. This ends "
            "your part of the conversation — do not call anything after it."
        ),
        parameters={
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "One short sentence for the agent picking this up.",
                }
            },
            "required": ["reason"],
            "additionalProperties": False,
        },
        fn=escalation_service.handoff,
    ),
]

BY_NAME: dict[str, Tool] = {t.name: t for t in TOOLS}


def tool_schemas(allowed: list[str] | None = None) -> list[dict]:
    """The allowed-tool list is per route. The FAQ handler gets *no* tools."""
    tools = TOOLS if allowed is None else [t for t in TOOLS if t.name in allowed]
    return [t.schema() for t in tools]
