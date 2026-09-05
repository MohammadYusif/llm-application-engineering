"""Refusals are product surface, not error handling.

One designed template per guard class, in both languages, reviewed to the same
standard as any answer. A good refusal keeps the citizen; a raw one loses them.

Two rules encoded here rather than left to memory:

* **never echo the offending text.** Reflected injection and log poisoning are the
  same mistake made twice; the refusal is a constant, and the log gets the verdict
  and a hash, never the payload.
* **never accuse.** Most people who trip a guard are curious, not hostile, and the
  ones who are hostile are not discouraged by a stern tone.
"""

from __future__ import annotations

REFUSALS: dict[str, dict[str, str]] = {
    "injection_pattern": {
        "ar": "أستطيع مساعدتك في الخدمات الحكومية. كيف يمكنني خدمتك اليوم؟",
        "en": "I can help with government services. How can I assist you today?",
    },
    "injection_attempt": {
        "ar": "أستطيع مساعدتك في الخدمات الحكومية. كيف يمكنني خدمتك اليوم؟",
        "en": "I can help with government services. How can I assist you today?",
    },
    "off_scope": {
        "ar": (
            "هذا خارج نطاق خدمتي — أنا هنا للمساعدة في الخدمات الحكومية. "
            "يمكنك سؤالي عن المواعيد أو الرسوم أو حالة الطلبات."
        ),
        "en": (
            "That is outside what I can help with — I am here for government "
            "services. Try asking about appointments, fees, or application status."
        ),
    },
    "crisis": {
        "ar": (
            "يؤسفني ما تمرّ به، وأنت لست وحدك. سأحوّلك الآن إلى موظف مختص يمكنه "
            "مساعدتك مباشرة. وإن كنت في خطر عاجل فاتصل بالرقم ٩٩٧ فوراً."
        ),
        "en": (
            "I am sorry you are going through this, and you are not alone. I am "
            "transferring you to a person who can help. If you are in immediate "
            "danger, please call 997 right now."
        ),
    },
    "too_long": {
        "ar": "الرسالة طويلة جداً. هل يمكنك تلخيص طلبك في بضعة أسطر؟",
        "en": "That message is longer than I can take in. Could you summarise your request in a few lines?",
    },
    "system_prompt_leak": {
        "ar": "لا أستطيع مشاركة إعدادات النظام. كيف يمكنني مساعدتك في خدمتك الحكومية؟",
        "en": "I can't share system configuration. How can I help with your government service?",
    },
    "pii_outbound": {
        "ar": "لا أستطيع عرض بيانات شخصية في هذه المحادثة. يمكنك مراجعتها في حسابك على البوابة.",
        "en": "I can't show personal data in this conversation. You can view it in your portal account.",
    },
    "unavailable": {
        "ar": "أعتذر، لا أستطيع الإجابة في هذه اللحظة. يمكنك مراجعة مركز الخدمة أو المحاولة لاحقاً.",
        "en": "I can't answer right now. Please try again shortly, or contact the service centre.",
    },
}


def refusal_for(category: str, language: str = "en") -> str:
    template = REFUSALS.get(category) or REFUSALS["off_scope"]
    return template.get(language, template["en"])
