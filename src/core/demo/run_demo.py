# src/core/demo/run_demo.py

from __future__ import annotations
import pprint

from core.data.demo_videos import VIDEO_DIE_ROLLER, VIDEO_RUBBER_ROLLER
from core.data.kb_builders import build_kb_from_two_videos
from core.ks.types import KSId, KSType
from core.runtime.world import Context
from core.query.parser import parse_query_to_ir1
from core.query.resolver import resolve_ir1_to_ir2
from core.runtime.reasoner import Reasoner
from core.query.ir import AnswerBundle

def pretty_print_answer(ans: AnswerBundle) -> None:
    print("=" * 100)
    print(f"Intent: {ans.intent.value}")
    print(f"Procedure: {ans.procedure_title}")
    print("-" * 100)
    for i, item in enumerate(ans.items, 1):
        print(f"[{i}] {pprint.pformat(item, width=120)}")
    print("-" * 100)
    print("Trace:")
    for k, v in ans.trace.items():
        print(f"  - {k}: {pprint.pformat(v, width=140)}")
    print("=" * 100)
    print()

def run_demo() -> None:
    kb, cloud_id = build_kb_from_two_videos(VIDEO_DIE_ROLLER, VIDEO_RUBBER_ROLLER)

    ctx_all = Context(mode="maintenance", available_tools=set(kb.tools.keys()))
    ctx_no_brush = Context(mode="maintenance", available_tools=set(kb.tools.keys()) - {KSId(KSType.TOOL, "NonMetalBrush")})

    reasoner = Reasoner(kb)

    queries = [
        # ("Bagian apa yang harus dibuka sebelum melepas die roller?", ctx_all),
        ("Sebelum memasang kembali die roller, apa yang harus dilakukan?", ctx_all),
        ("Bagaimana cara membersihkan die roller?", ctx_no_brush),  # show DR2 validator effect
    ]

    for q, ctx in queries:
        print(f"USER QUERY: {q} | ctx.mode={ctx.mode} | tools={len(ctx.available_tools)}")
        ir1 = parse_query_to_ir1(q)
        ir2 = resolve_ir1_to_ir2(kb, cloud_id, ir1, ctx=ctx)
        ans = reasoner.answer(ir2)
        pretty_print_answer(ans)

if __name__ == "__main__":
    run_demo()
