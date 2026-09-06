"""demo_v0 — the chatbot that works on stage.

    python demo_v0.py "How do I renew my commercial licence?"

Sixty lines, one afternoon, and it demonstrates beautifully. It is also where
Lab 1 starts: read it and list what would break in production, before anything
below names the failure modes for you. Most of them are findable from the code
alone, which is why the list is not printed here.

Six defects are marked `# SMELL`. There are more than six. Write your own list
before you read the markers — the list you produce is worth more than the one you
agree with.

Nothing in this file is imported by the application. It exists to be deleted, and
the commit that deletes it is the first commit of the course.
"""

import os
import sys

from openai import OpenAI  # SMELL 1: the application imports the provider SDK

client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8080/v1"),
    api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
)

SYSTEM = """You are Murshid, the assistant for the Kingdom's citizen-services portal.
Answer questions about government services. Be helpful and friendly. Fees for a
commercial registration renewal are SAR 200 per year. A national ID renewal is SAR
100. A driving licence renewal is SAR 40 per year."""
# SMELL 2: the prompt is a string literal in code — unversioned, unreviewable, and
#          the service facts are baked into it, so a fee change is a code deploy.

history = []  # SMELL 3: unbounded. Every turn resends everything, forever.


def ask(question: str) -> str:
    history.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model="course-flagship",  # SMELL 4: a literal model id, in code
        messages=[{"role": "system", "content": SYSTEM}] + history,
        temperature=0.7,
        # SMELL 5: no max_tokens, no timeout, no retry policy. The demo defaults
        #          that become the production incident.
    )
    answer = response.choices[0].message.content
    # SMELL 6: finish_reason is never read. A truncated answer ships silently, and
    #          a refusal arrives as an empty string nobody handles.
    history.append({"role": "assistant", "content": answer})
    return answer


def main() -> None:
    if len(sys.argv) > 1:
        print(ask(" ".join(sys.argv[1:])))
        return
    print("murshid demo_v0 — Ctrl-C to leave\n")
    while True:
        try:
            question = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if question:
            print("murshid>", ask(question))


if __name__ == "__main__":
    main()
