"""The output contract's semantics, and the state that holds authority.

Two halves of the same lesson. The schema guarantees the shape; the validators
guarantee the meaning; the session guarantees who it is for. Nothing in a token
stream guarantees any of the three.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from murshid.domain.session import ConversationState, Session, contains_pii, mask_pii
from murshid.domain.ticket import (
    Applicant,
    BookingRequest,
    ServiceTicket,
    schema_violations,
    strict_schema,
)


def valid_ticket(**overrides) -> dict:
    payload = {
        "service_type": "commercial_licence",
        "summary_en": "Citizen asks about renewing a commercial registration.",
        "city": "Riyadh",
        "urgency": "routine",
        "language": "ar",
        "applicant": {"full_name": "Unnamed citizen", "national_id": None, "phone": None},
        "needs_human": False,
    }
    payload.update(overrides)
    return payload


def test_a_well_formed_ticket_validates():
    ticket = ServiceTicket(**valid_ticket())
    assert ticket.city == "Riyadh"
    assert ticket.applicant.national_id is None


@pytest.mark.parametrize(
    "national_id",
    ["912345678", "31234567890", "9123456789", "abcdefghij", "112345678"],
)
def test_the_national_id_validator_rejects_what_the_schema_cannot(national_id: str):
    """Constrained decoding produces a string. Only a validator knows what a
    Saudi national ID is."""
    with pytest.raises(ValidationError):
        Applicant(full_name="x", national_id=national_id)


def test_a_valid_national_id_passes():
    assert Applicant(full_name="x", national_id="1098765432").national_id == "1098765432"
    assert Applicant(full_name="x", national_id="2011223344").national_id == "2011223344"


@pytest.mark.parametrize("city", ["Al Khobar", "riyadh", "RIYADH", ""])
def test_an_out_of_enum_city_is_rejected(city: str):
    with pytest.raises(ValidationError):
        ServiceTicket(**valid_ticket(city=city))


def test_extra_fields_are_forbidden():
    with pytest.raises(ValidationError):
        ServiceTicket(**valid_ticket(confidence=0.9))


def test_the_wire_schema_fits_the_strict_subset():
    assert schema_violations(strict_schema()) == []
    schema = strict_schema()["json_schema"]
    assert schema["strict"] is True
    assert schema["schema"]["additionalProperties"] is False


def working_day(days: int = 30) -> date:
    day = date.today() + timedelta(days=days)
    while day.weekday() in (4, 5):
        day += timedelta(days=1)
    return day


def test_the_booking_contract_enforces_business_rules():
    assert BookingRequest(
        service_type="civil_records", city="Riyadh", date=working_day()
    ).city == "Riyadh"

    with pytest.raises(ValidationError, match="future"):
        BookingRequest(service_type="civil_records", city="Riyadh", date=date(2019, 1, 2))

    friday = date.today() + timedelta(days=(4 - date.today().weekday()) % 7 + 7)
    with pytest.raises(ValidationError, match="closed"):
        BookingRequest(service_type="civil_records", city="Riyadh", date=friday)

    with pytest.raises(ValidationError, match="60 days"):
        BookingRequest(service_type="civil_records", city="Riyadh", date=working_day(120))


# --- conversation state ---------------------------------------------------


def test_the_window_forgets_the_oldest_turn():
    """The moment statelessness lands: turn one is gone after turn nine."""
    state = ConversationState(max_turns=8)
    for i in range(9):
        state.add_user(f"question {i}")
        state.add_assistant(f"answer {i}")

    contents = [m.content for m in state.turns]
    assert "question 0" not in contents
    assert "question 8" in contents
    assert len(state.turns) == 16


def test_history_replays_oldest_to_newest_after_the_system_prompt():
    state = ConversationState()
    state.add_user("first")
    state.add_assistant("reply")
    messages = state.messages(system="SYSTEM")
    assert [m.role for m in messages] == ["system", "user", "assistant"]
    assert messages[1].content == "first"


# --- authority ------------------------------------------------------------


def test_the_session_not_the_argument_decides_whose_booking_it_is():
    session = Session(citizen_id="citizen-A")
    verdict = session.authorize("book_appointment", {"city": "Riyadh", "on_behalf_of": "citizen-B"})
    assert not verdict.allowed
    assert verdict.reason == "cross_citizen"
    assert verdict.user_hint


def test_stale_verification_blocks_a_side_effect():
    session = Session(citizen_id="citizen-A", identity_verified=False)
    assert not session.authorize("book_appointment", {"city": "Riyadh"}).allowed
    session.verify_identity()
    assert session.authorize("book_appointment", {"city": "Riyadh"}).allowed


def test_idempotency_blocks_the_second_identical_booking():
    session = Session()
    args = {"service_type": "civil_records", "city": "Riyadh", "date": "2026-10-14"}
    assert session.authorize("book_appointment", args).allowed
    session.record_side_effect("book_appointment", args, {"confirmation": "AP1"})
    assert not session.authorize("book_appointment", args).allowed
    assert session.replay_side_effect("book_appointment", args) == {"confirmation": "AP1"}


def test_the_pii_vault_round_trips_inside_the_boundary():
    session = Session()
    masked = mask_pii("id 1098765432 phone +966512345678 iban SA0380000000608010167519", session)
    assert contains_pii(masked) is None
    assert "1098765432" in session.pii_vault.unmask(masked)
