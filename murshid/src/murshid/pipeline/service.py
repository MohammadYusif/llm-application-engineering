"""The service workflow: the route that *acts*.

It is a workflow with a bounded tool loop inside it, not an agent — the steps are
known at design time, so the decomposition is fixed and only the tool choices are
the model's. That is the escalation ladder's advice taken: stay as low as the use
case allows.
"""

from __future__ import annotations

import time
from datetime import date

from murshid.domain.directory import rendered_directory
from murshid.domain.session import Session
from murshid.guards.input_guards import GuardedInput
from murshid.llm.interfaces import LLMClient, Message
from murshid.observability import current_trace_id, get_logger
from murshid.pipeline.tool_loop import run_with_tools
from murshid.pipeline.types import Reply
from murshid.prompts.registry import load_prompt

log = get_logger(__name__)

SERVICE_PROMPT_REF = "service_workflow.v2"
ALLOWED_TOOLS = ["check_application_status", "book_appointment", "escalate_to_agent"]


class ServiceWorkflow:
    def __init__(
        self,
        client: LLMClient,
        *,
        model_alias: str = "murshid-default",
        prompt_ref: str = SERVICE_PROMPT_REF,
        max_iterations: int = 6,
        meter=None,
    ) -> None:
        self._client = client
        self._model_alias = model_alias
        self._prompt = load_prompt(prompt_ref)
        self._max_iterations = max_iterations
        self._meter = meter

    @property
    def prompt_version(self) -> str:
        return self._prompt.ref

    def run(self, guarded: GuardedInput, session: Session) -> Reply:
        t0 = time.perf_counter()
        language = guarded.language
        directory = rendered_directory("ar" if language == "ar" else "en")
        system = self._prompt.render(
            service_directory=directory, today=date.today().isoformat()
        )
        messages = [
            Message(role="system", content=system),
            *session.state.messages(),
            Message(role="user", content=f"<citizen_message>\n{guarded.text}\n</citizen_message>"),
        ]

        outcome = run_with_tools(
            self._client,
            messages,
            session,
            allowed_tools=ALLOWED_TOOLS,
            model_alias=self._model_alias,
            max_iterations=self._max_iterations,
            language=language,
        )

        cost = 0.0
        input_tokens = cached = output_tokens = 0
        model_id = route = ""
        for response in outcome.responses:
            model_id = response.model_id or model_id
            route = response.route or route
            input_tokens += response.usage.input_tokens
            cached += response.usage.cached_input_tokens
            output_tokens += response.usage.output_tokens
            if self._meter is not None:
                record = self._meter.meter(
                    response,
                    route=response.route or self._model_alias,
                    intent="service",
                    stage="service_workflow",
                    prompt_version=self._prompt.ref,
                )
                cost += record.cost_halalas

        return Reply(
            text=outcome.text,
            intent="service",
            language=language,
            route=route,
            model_id=model_id,
            prompt_version=self._prompt.ref,
            tool_calls=outcome.calls,
            tool_iterations=outcome.iterations,
            escalated=outcome.escalated,
            latency_ms=(time.perf_counter() - t0) * 1000,
            cost_halalas=round(cost, 6),
            input_tokens=input_tokens,
            cached_tokens=cached,
            output_tokens=output_tokens,
            trace_id=current_trace_id(),
            degraded=outcome.bound_hit,
        )
