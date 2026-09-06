"""``ServiceTicket`` — the structured object Murshid files into the case system.

The division of labour Module 3 is about:

* the **JSON Schema** constrains *syntax* — the provider's strict mode guarantees
  the shape, the enums and that no extra keys appear;
* **pydantic validators** enforce *semantics* — that a national ID is ten digits
  starting 1 or 2, that a booking date is a future working day. Constrained
  decoding cannot know either of those things.

Belt and suspenders, each doing a different job. Which means validation can still
fail, which means the application still needs a designed failure path.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CITIES = (
    "Riyadh",
    "Jeddah",
    "Makkah",
    "Dammam",
    "Madinah",
    "Abha",
    "Tabuk",
    "Buraidah",
    "unknown",
)
SERVICE_TYPES = (
    "commercial_licence",
    "civil_records",
    "traffic_services",
    "municipal_permits",
    "other",
)


class Applicant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(description="Name exactly as given by the citizen")
    national_id: str | None = Field(
        None, description="Saudi national ID or Iqama, 10 digits, if the citizen provided one"
    )
    phone: str | None = Field(None, description="Phone in +9665XXXXXXXX form, if provided")

    @field_validator("national_id")
    @classmethod
    def valid_national_id(cls, v: str | None) -> str | None:
        if v is not None and not (len(v) == 10 and v.isdigit() and v[0] in "12"):
            raise ValueError("must be 10 digits starting with 1 (citizen) or 2 (resident)")
        return v

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = v.replace(" ", "").replace("-", "")
        if not (digits.startswith(("+9665", "05", "9665")) and sum(c.isdigit() for c in digits) >= 9):
            raise ValueError("must be a Saudi mobile number, e.g. +9665XXXXXXXX")
        return digits


class ServiceTicket(BaseModel):
    """Extracted from a free-text citizen message.

    Fields the message does not contain are ``None`` — the model must NOT invent
    them, and ``make extract-audit`` measures whether it did.
    """

    model_config = ConfigDict(extra="forbid")

    service_type: Literal[
        "commercial_licence",
        "civil_records",
        "traffic_services",
        "municipal_permits",
        "other",
    ]
    summary_en: str = Field(description="One-sentence English summary for the case system")
    city: Literal[
        "Riyadh",
        "Jeddah",
        "Makkah",
        "Dammam",
        "Madinah",
        "Abha",
        "Tabuk",
        "Buraidah",
        "unknown",
    ]
    urgency: Literal["routine", "urgent", "emergency"]
    language: Literal["ar", "en", "mixed"]
    applicant: Applicant
    needs_human: bool = Field(
        description="True if the request cannot be served by self-service"
    )


def strict_schema(model: type[BaseModel] = ServiceTicket, name: str = "service_ticket") -> dict:
    """What goes over the wire, in the strict-mode subset.

    Strict mode is narrower than JSON Schema: objects must be closed
    (``additionalProperties: false``) and *every* property must be listed as
    required — optional fields are expressed as a nullable type, never by absence.
    ``make schema-check`` fails the build when a contract drifts out of the subset.
    """
    schema = model.model_json_schema()
    _tighten(schema, schema)
    # The contract's name travels *inside* the schema as well as beside it, so an
    # adapter whose dialect has no name field (Anthropic's output_config) does not
    # lose it. Small thing; it is the difference between one code path and two.
    schema["title"] = name
    return {"type": "json_schema", "json_schema": {"name": name, "strict": True, "schema": schema}}


def _tighten(node: dict, root: dict) -> None:
    if not isinstance(node, dict):
        return
    for sub in node.get("$defs", {}).values():
        _tighten(sub, root)
    if node.get("type") == "object" or "properties" in node:
        node["additionalProperties"] = False
        node["required"] = sorted(node.get("properties", {}))
    for value in node.get("properties", {}).values():
        _tighten(value, root)
    for key in ("items", "anyOf", "allOf", "oneOf"):
        value = node.get(key)
        if isinstance(value, list):
            for item in value:
                _tighten(item, root)
        elif isinstance(value, dict):
            _tighten(value, root)


TICKET_SCHEMA = strict_schema()


def schema_violations(schema: dict) -> list[str]:
    """Human-readable reasons a schema would be rejected by strict mode."""
    problems: list[str] = []

    def walk(node, path="$"):
        if not isinstance(node, dict):
            return
        for name, sub in node.get("$defs", {}).items():
            walk(sub, f"$defs.{name}")
        if node.get("type") == "object" or "properties" in node:
            if node.get("additionalProperties") is not False:
                problems.append(f"{path}: object is open (needs additionalProperties: false)")
            declared = set(node.get("properties", {}))
            required = set(node.get("required", []))
            if declared - required:
                missing = ", ".join(sorted(declared - required))
                problems.append(f"{path}: properties not listed as required ({missing})")
        for key, sub in node.get("properties", {}).items():
            walk(sub, f"{path}.{key}")

    walk(schema.get("json_schema", {}).get("schema", schema))
    return problems


class BookingRequest(BaseModel):
    """The side-effecting tool's argument contract. Validated before anything runs."""

    model_config = ConfigDict(extra="forbid")

    service_type: Literal[
        "commercial_licence", "civil_records", "traffic_services", "municipal_permits"
    ]
    city: Literal[
        "Riyadh", "Jeddah", "Makkah", "Dammam", "Madinah", "Abha", "Tabuk", "Buraidah"
    ]
    #: Named for the tool's argument, annotated through the module alias so the
    #: field name cannot shadow the type. A small trap, and a real one.
    date: dt.date = Field(description="YYYY-MM-DD, must be a future working day")

    @field_validator("date")
    @classmethod
    def future_working_day(cls, v: dt.date) -> dt.date:
        if v <= dt.date.today():
            raise ValueError("appointment date must be in the future")
        if v > dt.date.today() + dt.timedelta(days=60):
            raise ValueError("appointments open 60 days ahead at most")
        if v.weekday() in (4, 5):  # Friday, Saturday
            raise ValueError("service centres are closed on Friday and Saturday")
        return v
