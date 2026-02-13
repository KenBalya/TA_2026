# src/core/query/resolver.py

from __future__ import annotations
from typing import Optional

from core.ks.types import KSId, KSType
from core.kb.knowledge_base import KnowledgeBase
from core.query.ir import QueryIR1, QueryIR2, IntentType
from core.runtime.world import Context

def resolve_ir1_to_ir2(kb: KnowledgeBase, cloud_id: KSId, ir1: QueryIR1, ctx: Optional[Context] = None) -> QueryIR2:
    ctx = ctx or Context()

    # default: assume all tools available (so it won't falsely fail)
    if not ctx.available_tools:
        ctx.available_tools = set(kb.tools.keys())

    if not ir1.procedure_hint:
        proc_id = kb.clouds[cloud_id].procedure_ids[0]
    else:
        proc_id = kb.procedure_by_hint(ir1.procedure_hint) or kb.clouds[cloud_id].procedure_ids[0]

    anchor_step_id = None
    if ir1.intent in {IntentType.PRECONDITION, IntentType.NEXT_STEP} and ir1.anchor_verb and ir1.anchor_object:
        anchor_step_id = kb.find_step_by_anchor(proc_id, ir1.anchor_verb, ir1.anchor_object)

    target_entity = None
    if ir1.intent == IntentType.WHERE and ir1.target_token:
        tool_cands = kb.resolve_tool_candidates(ir1.target_token, scope_proc=proc_id)
        comp_cands = kb.resolve_component_candidates(ir1.target_token, scope_proc=proc_id)
        if tool_cands and (not comp_cands or tool_cands[0].score >= comp_cands[0].score):
            target_entity = tool_cands[0].id
        elif comp_cands:
            target_entity = comp_cands[0].id

    return QueryIR2(
        intent=ir1.intent,
        cloud_id=cloud_id,
        procedure_id=proc_id,
        anchor_step_id=anchor_step_id,
        temporal_relation=ir1.temporal_relation,
        focus=ir1.focus,
        target_entity=target_entity,
        ctx=ctx,
    )
