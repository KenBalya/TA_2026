# src/core/query/parser.py

from __future__ import annotations

from core.utils.text import norm_text
from core.query.ir import QueryIR1, IntentType, QuestionFocus

def parse_query_to_ir1(q: str) -> QueryIR1:
    nq = norm_text(q)

    proc_hint = None
    if "die roller" in nq:
        proc_hint = "die roller"
    elif "rubber" in nq or "roller karet" in nq or "s1s" in nq:
        proc_hint = "rubber roller"

    target_token = None
    if "aqua" in nq or "demineral" in nq:
        target_token = "aqua de mineral"
    if "s1s" in nq:
        target_token = "s1s"

    if "bagian apa" in nq and ("dibuka" in nq or "buka" in nq) and ("sebelum" in nq):
        return QueryIR1(
            intent=IntentType.PRECONDITION,
            procedure_hint=proc_hint,
            anchor_verb="melepas" if "lepas" in nq or "melepas" in nq else "memasang kembali",
            anchor_object="die roller" if "die roller" in nq else "rubber roller",
            temporal_relation="BEFORE",
            focus=QuestionFocus.COMPONENT_TO_OPEN,
        )

    if "sebelum" in nq:
        anchor_verb = "memasang" if ("pasang" in nq) else ("melepas" if "lepas" in nq else None)
        anchor_object = "die roller" if "die roller" in nq else ("rubber roller" if "rubber" in nq or "roller karet" in nq else None)
        return QueryIR1(
            intent=IntentType.PRECONDITION,
            procedure_hint=proc_hint,
            anchor_verb=anchor_verb,
            anchor_object=anchor_object,
            temporal_relation="BEFORE",
            focus=QuestionFocus.STEPS,
        )

    if "bagaimana" in nq or "gimana" in nq or "cara" in nq:
        return QueryIR1(intent=IntentType.HOW_TO, procedure_hint=proc_hint, focus=QuestionFocus.STEPS)

    if "langkah mana" in nq or "di langkah" in nq or "di segmen" in nq or "timestamp" in nq:
        return QueryIR1(intent=IntentType.WHERE, procedure_hint=proc_hint, focus=QuestionFocus.EVIDENCE, target_token=target_token)

    if "setelah" in nq or "next" in nq or "langkah berikut" in nq:
        return QueryIR1(intent=IntentType.NEXT_STEP, procedure_hint=proc_hint, focus=QuestionFocus.STEPS)

    return QueryIR1(intent=IntentType.UNKNOWN, procedure_hint=proc_hint, focus=QuestionFocus.UNKNOWN, target_token=target_token)
