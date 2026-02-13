# tests/test_smoke.py

from core.data.demo_videos import VIDEO_DIE_ROLLER, VIDEO_RUBBER_ROLLER
from core.data.kb_builders import build_kb_from_two_videos
from core.runtime.world import Context
from core.query.parser import parse_query_to_ir1
from core.query.resolver import resolve_ir1_to_ir2
from core.runtime.reasoner import Reasoner

def test_smoke_end_to_end():
    kb, cloud_id = build_kb_from_two_videos(VIDEO_DIE_ROLLER, VIDEO_RUBBER_ROLLER)
    ctx = Context(mode="maintenance", available_tools=set(kb.tools.keys()))
    reasoner = Reasoner(kb)

    q = "Bagaimana cara membersihkan rubber roller?"
    ir1 = parse_query_to_ir1(q)
    ir2 = resolve_ir1_to_ir2(kb, cloud_id, ir1, ctx=ctx)
    ans = reasoner.answer(ir2)

    assert ans.intent.value in {"HOW_TO", "PRECONDITION", "WHERE", "NEXT_STEP", "UNKNOWN"}
    assert ans.procedure_title
    assert isinstance(ans.items, list)
