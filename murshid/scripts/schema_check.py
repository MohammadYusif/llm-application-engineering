"""Does every output contract still fit the strict-mode subset?

    python scripts/schema_check.py

Strict mode is narrower than JSON Schema: closed objects, every property listed as
required, optionality expressed as a nullable type. A contract that drifts out of
the subset fails at the provider, at run time, on a Tuesday. This runs in CI.
"""

from __future__ import annotations

from _common import bootstrap, rule

bootstrap()

from murshid.domain.ticket import (  # noqa: E402
    Applicant,
    BookingRequest,
    ServiceTicket,
    schema_violations,
    strict_schema,
)
from murshid.guards.input_guards import ScopeVerdict  # noqa: E402
from murshid.pipeline.router import RouteVerdict  # noqa: E402

CONTRACTS = [
    (ServiceTicket, "service_ticket"),
    (Applicant, "applicant"),
    (BookingRequest, "booking_request"),
    (ScopeVerdict, "guard_verdict"),
    (RouteVerdict, "route_verdict"),
]


def main() -> int:
    rule("schema-check | strict-mode subset")
    bad = 0
    for model, name in CONTRACTS:
        problems = schema_violations(strict_schema(model, name))
        bad += 1 if problems else 0
        print(f"  {'OK ' if not problems else 'BAD'} {name}")
        for problem in problems:
            print(f"      {problem}")
    print(f"\n{len(CONTRACTS) - bad}/{len(CONTRACTS)} contracts strict-safe")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
