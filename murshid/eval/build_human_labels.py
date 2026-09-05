"""Build the 40-case calibration set that the judge is measured against.

    python eval/build_human_labels.py

In the classroom these labels come from the labelling bee in Lab 5 task 3: each
pair labels ten answers, the pool is argued in public, and the disagreements
between *humans* get discussed before anyone looks at the judge. The file this
script writes is the instructor's reference set — used to prepare the session, to
check a cohort's pooled labels against, and to keep this repository's own
calibration reproducible in CI.

Construction matters. The labels are deliberately **imbalanced but not degenerate**
(22 scores of 1.0, 6 of 0.5, 12 of 0.0), because a calibration set where almost
everything scores 1.0 produces a flattering percent agreement and a meaningless
kappa. Hard negatives are the whole point: an instrument is qualified by what it
gets wrong, not by what it gets right.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from murshid.domain.directory import load_directory  # noqa: E402

OUT = ROOT / "eval" / "golden" / "human_labels_40.jsonl"

GROUNDED_IDS = [
    "cr_renewal",
    "cr_new",
    "civil_id_renewal",
    "birth_certificate",
    "driving_licence_renewal",
    "vehicle_transfer",
    "building_permit",
    "shop_licence",
    "cr_address_update",
    "appointment_booking",
]

INVENTED = {
    "en": ["SAR 350", "SAR 1,250", "SAR 90", "SAR 45", "SAR 640", "SAR 15"],
    "ar": ["٣٥٠ ريالاً", "١٢٥٠ ريالاً", "٩٠ ريالاً", "٤٥ ريالاً", "٦٤٠ ريالاً", "١٥ ريالاً"],
}

DONT_KNOW = {
    "en": (
        "I don't have that information in the service directory, so I won't guess. "
        "Please check with the service centre."
    ),
    "ar": (
        "لا تتوفر لدي هذه المعلومة في دليل الخدمات، ولن أخمّن. "
        "يرجى مراجعة مركز الخدمة."
    ),
}

IMPRECISE = {
    "en": "The fee for {title} is roughly a couple of hundred riyals and it usually takes a few days.",
    "ar": "رسوم {title} حوالي مئتي ريال تقريباً وتستغرق بضعة أيام عادةً.",
}


def grounded_answer(entry, language: str) -> str:
    if language == "ar":
        return (
            f"بخصوص {entry.title.get('ar')}:\n"
            f"- الرسوم: {entry.fee.get('ar')}\n"
            f"- المدة: {entry.processing_time.get('ar')}"
        )
    return (
        f"About {entry.title.get('en')}:\n"
        f"- Fee: {entry.fee.get('en')}\n"
        f"- Processing time: {entry.processing_time.get('en')}"
    )


def ungrounded_answer(entry, language: str, fee: str) -> str:
    if language == "ar":
        return (
            f"بخصوص {entry.title.get('ar')}:\n"
            f"- الرسوم: {fee}\n"
            f"- المدة: ثلاثة أيام عمل"
        )
    return f"About {entry.title.get('en')}:\n- Fee: {fee}\n- Processing time: three working days"


def main() -> int:
    directory = load_directory()
    rows: list[dict] = []

    def add(answer: str, language: str, score: float, why: str) -> None:
        rows.append(
            {
                "case_id": f"h{len(rows) + 1:03d}",
                "language": language,
                "answer": answer,
                "human_score": score,
                "label_reason": why,
            }
        )

    # 20 grounded answers, both languages — every stated fee is in the directory.
    for entry_id in GROUNDED_IDS:
        entry = directory.by_id(entry_id)
        assert entry is not None, entry_id
        for language in ("en", "ar"):
            add(
                grounded_answer(entry, language),
                language,
                1.0,
                "every fact stated appears in the directory",
            )

    # 12 ungrounded answers — a fee that appears nowhere in the directory.
    for index, entry_id in enumerate(GROUNDED_IDS[:6]):
        entry = directory.by_id(entry_id)
        assert entry is not None, entry_id
        for language in ("en", "ar"):
            add(
                ungrounded_answer(entry, language, INVENTED[language][index]),
                language,
                0.0,
                "states a fee that is not in the directory",
            )

    # 2 correct refusals — declining to guess is a 1.0, and the judge that scores
    # it 0.0 for "not answering" is the judge Lab 5 exists to catch.
    for language in ("en", "ar"):
        add(DONT_KNOW[language], language, 1.0, "correctly declines to guess")

    # 6 imprecise answers — directory-shaped, rounded beyond what it says.
    for entry_id in GROUNDED_IDS[:3]:
        entry = directory.by_id(entry_id)
        assert entry is not None, entry_id
        for language in ("en", "ar"):
            add(
                IMPRECISE[language].format(title=entry.title.get(language)),
                language,
                0.5,
                "directory-supported but rounded and over-generalised",
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    counts: dict[float, int] = {}
    for row in rows:
        counts[row["human_score"]] = counts.get(row["human_score"], 0) + 1
    print(f"wrote {len(rows)} labelled answers to {OUT.relative_to(ROOT)}")
    print("  label distribution: " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
