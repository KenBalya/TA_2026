# src/core/runtime/simulate.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

import copy

from core.ks.types import KSId, ActionType
from core.ks.entities import Step
from core.rules.drels import DRelEffectType
from core.kb.knowledge_base import KnowledgeBase
from core.runtime.world import Context, WorldState

@dataclass
class StepSnapshot:
    step_id: KSId
    before: WorldState
    after: WorldState
    valid: bool
    reasons: List[str]

def apply_drels_runtime(kb: KnowledgeBase, proc_id: KSId, ctx: Context, world: WorldState) -> Dict[KSId, Step]:
    steps_view: Dict[KSId, Step] = {}
    lot = kb.procedures[proc_id].lot
    for sid in lot:
        steps_view[sid] = copy.deepcopy(kb.steps[sid])

    for d in kb.drels:
        if not d.condition(ctx, world):
            continue

        # apply to a specific step
        if d.target_step and d.target_step in steps_view:
            st = steps_view[d.target_step]
            if d.effect_type == DRelEffectType.INJECT_STEP_PRECONDITION and isinstance(d.payload, KSId):
                if d.payload not in st.preconditions:
                    st.preconditions.append(d.payload)
            elif d.effect_type == DRelEffectType.INJECT_STEP_TOOL and isinstance(d.payload, KSId):
                if d.payload not in st.tools:
                    st.tools.append(d.payload)
            elif d.effect_type == DRelEffectType.ADD_VALIDATOR and callable(d.payload):
                st.validators.append(d.payload)
            continue

        # procedure-wide by action type
        if d.target_procedure is None and d.target_step is None:
            if d.effect_type == DRelEffectType.INJECT_STEP_PRECONDITION and isinstance(d.payload, KSId):
                for _, st in steps_view.items():
                    if st.action_type in {ActionType.OPEN_COVER, ActionType.REMOVE_COMPONENT, ActionType.CLEAN_COMPONENT, ActionType.CLEAN_AREA}:
                        if d.payload not in st.preconditions:
                            st.preconditions.append(d.payload)

    return steps_view

def simulate_forward(kb: KnowledgeBase, proc_id: KSId, steps_view: Dict[KSId, Step], ctx: Context, initial: Optional[WorldState] = None) -> List[StepSnapshot]:
    world = copy.deepcopy(initial) if initial else WorldState(states=set(), slots={})
    snaps: List[StepSnapshot] = []
    for sid in kb.procedures[proc_id].lot:
        st = steps_view[sid]
        before = copy.deepcopy(world)
        ok, reasons = st.validate(ctx, world)
        if ok:
            st.apply(ctx, world)
        after = copy.deepcopy(world)
        snaps.append(StepSnapshot(step_id=sid, before=before, after=after, valid=ok, reasons=reasons))
    return snaps
