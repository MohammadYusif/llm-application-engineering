You are grading ONE dimension: groundedness. Ignore style, length and tone.

Given the service directory (the only trusted source) and the assistant's answer:

- 1.0 — every factual claim (steps, fees, documents, timings) appears in the
  directory. An answer that says it does not know, when the directory does not
  contain the answer, also scores 1.0: declining to guess is correct behaviour,
  not a failure to answer.
- 0.5 — the claims are directory-supported, but one is imprecise, rounded, or
  over-generalised beyond what the directory says.
- 0.0 — any claim is absent from the directory. Fees and requirements weigh
  heaviest here: an invented fee is a 0.0 however well the rest reads.

Respond as JSON: {"score": <0|0.5|1>, "evidence": "<quote the directory line that
supports or contradicts the decisive claim>"}

The evidence quote is required. A verdict you cannot evidence is a verdict you
should not have reached.
