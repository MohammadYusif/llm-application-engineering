"""The negative tests. This file is the security model, executable.

Four attacks, four rules:

1. a conversation cannot book for somebody else — the *session* decides, not the
   model's arguments;
2. a hallucinated tool name is an error the model can recover from, not a crash;
3. malformed arguments never reach a function;
4. a stubborn model meets a bound, and the bound degrades by design.

Plus the one that costs real money when it is missing: a retried turn does not
book twice.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from murshid.llm.fake import FakeClient
from murshid.llm.interfaces import Message
from murshid.pipeline.tool_loop import run_with_tools
from murshid.tools.services import booking_service


def seed_messages() -> list[Message]:
    return [
        Message(role="system", content="You are Murshid."),
        Message(role="user", content="Please book me an appointment."),
    ]


def next_working_day(days_ahead: int = 30) -> str:
    day = date.today() + timedelta(days=days_ahead)
    while day.weekday() in (4, 5):  # Friday, Saturday
        day += timedelta(days=1)
    return day.isoformat()


def test_booking_for_someone_else_is_denied(fake_client: FakeClient, session):
    """The injected conversation asks to book on behalf of citizen B.

    The model's arguments are user input by proxy — they may have arrived through
    forty patient turns of conversation. The session, and only the session, says
    whose booking this is.
    """
    fake_client.script_tool_call(
        "book_appointment",
        {
            "service_type": "civil_records",
            "city": "Riyadh",
            "date": next_working_day(),
            "on_behalf_of": "citizen-B",
        },
    )
    fake_client.script_text("I could not do that.")

    result = run_with_tools(fake_client, seed_messages(), session)

    assert booking_service.bookings_for("citizen-B") == []
    assert booking_service.bookings_for("citizen-A") == []
    assert result.calls == [], "a denied call never reaches the function"


def test_hallucinated_tool_name_is_an_error_not_a_crash(fake_client: FakeClient, session):
    fake_client.script_tool_call("cancel_everything", {"reason": "why not"})
    fake_client.script_text("Sorry, I cannot do that.")

    result = run_with_tools(fake_client, seed_messages(), session)

    assert result.text == "Sorry, I cannot do that."
    assert result.calls == []


def test_malformed_arguments_never_reach_the_function(fake_client: FakeClient, session):
    fake_client.script_tool_call("check_application_status", "{not json at all")
    fake_client.script_text("Could you confirm the reference number?")

    result = run_with_tools(fake_client, seed_messages(), session)

    assert "reference" in result.text.lower()
    assert result.calls == []


def test_loop_bound_trips_to_designed_degradation(fake_client: FakeClient, session):
    """A failing tool retried thirty times is a denial-of-wallet attack you wrote."""
    fake_client.script_endless_tool_calls("check_application_status")

    result = run_with_tools(fake_client, seed_messages(), session, max_iterations=6)

    assert result.bound_hit is True
    assert "transferring you" in result.text
    assert fake_client.call_count == 6, "the bound is 6, not 30"


def test_a_retried_turn_does_not_book_twice(fake_client: FakeClient, session):
    """Side effects plus retries need idempotency, exactly as in any other
    distributed system. The second execution is blocked, and one booking exists."""
    booking = {
        "service_type": "civil_records",
        "city": "Riyadh",
        "date": next_working_day(),
    }
    fake_client.script_tool_call("book_appointment", booking)
    fake_client.script_text("Booked.")
    run_with_tools(fake_client, seed_messages(), session)

    replay = FakeClient()
    replay.script_tool_call("book_appointment", booking)
    replay.script_text("Booked.")
    run_with_tools(replay, seed_messages(), session)

    assert len(booking_service.bookings_for("citizen-A")) == 1


def test_a_past_date_is_rejected_by_the_argument_contract(fake_client: FakeClient, session):
    """Constrained decoding guarantees the shape. It cannot know that 2019 is over."""
    fake_client.script_tool_call(
        "book_appointment",
        {"service_type": "civil_records", "city": "Riyadh", "date": "2019-01-02"},
    )
    fake_client.script_text("That date has passed — which day would suit you?")

    result = run_with_tools(fake_client, seed_messages(), session)

    assert booking_service.bookings_for("citizen-A") == []
    assert "date" in result.text.lower()


def test_unverified_identity_blocks_a_side_effecting_tool(fake_client: FakeClient):
    from murshid.domain.session import Session

    unverified = Session(citizen_id="citizen-A", identity_verified=False)
    fake_client.script_tool_call(
        "book_appointment",
        {"service_type": "civil_records", "city": "Riyadh", "date": next_working_day()},
    )
    fake_client.script_text("I need to verify your identity first.")

    run_with_tools(fake_client, seed_messages(), unverified)

    assert booking_service.bookings_for("citizen-A") == []


def test_read_only_tools_need_no_gate(fake_client: FakeClient, session):
    fake_client.script_tool_call("check_application_status", {"reference": "CR12345678"})
    fake_client.script_text("It is under review.")

    result = run_with_tools(fake_client, seed_messages(), session)

    assert [call["tool"] for call in result.calls] == ["check_application_status"]
    assert result.calls[0]["risk"] == "read_only"


@pytest.mark.parametrize("tool_name", ["check_application_status", "book_appointment"])
def test_every_tool_call_is_traced_with_its_risk_class(fake_client: FakeClient, session, tool_name):
    arguments = (
        {"reference": "CR12345678"}
        if tool_name == "check_application_status"
        else {"service_type": "civil_records", "city": "Riyadh", "date": next_working_day()}
    )
    fake_client.script_tool_call(tool_name, arguments)
    fake_client.script_text("done")

    run_with_tools(fake_client, seed_messages(), session)

    assert session.tool_trace, "governance: 100% of calls logged with risk class and iteration"
    assert session.tool_trace[0]["tool"] == tool_name
    assert "risk" in session.tool_trace[0]
    assert session.tool_trace[0]["iteration"] == 1
