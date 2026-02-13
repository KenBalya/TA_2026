# src/core/runtime/reasoning.py

from __future__ import annotations
from typing import Any, Dict, List, Set, Tuple

from core.ks.types import KSId, KSType
from core.ks.entities import Step
from core.kb.knowledge_base import KnowledgeBase

def producers_of_state(kb: KnowledgeBase, proc_id: KSId, steps_view: Dict[KSId, Step], state_id: KSId) -> List[KSId]:
    prod = []
    for sid in kb.procedures[proc_id].lot:
        if state_id in steps_view[sid].postconditions:
            prod.append(sid)
    return prod

def backward_chain_minimal(kb: KnowledgeBase, proc_id: KSId, steps_view: Dict[KSId, Step], target_states: List[KSId]) -> Tuple[List[KSId], Dict[str, Any]]:
    needed_states = set([s for s in target_states if s.type == KSType.STATE])
    selected_steps: Set[KSId] = set()
    because: List[Dict[str, Any]] = []
    visited_states: Set[KSId] = set()

    def solve_state(s: KSId) -> None:
        if s in visited_states:
            return
        visited_states.add(s)
        prod_steps = producers_of_state(kb, proc_id, steps_view, s)
        if not prod_steps:
            because.append({"need_state": str(s), "note": "no_producer_assumed_initial_or_external"})
            return

        prod_steps_sorted = sorted(prod_steps, key=lambda sid: kb.lot_index(proc_id, sid))
        chosen = prod_steps_sorted[0]
        selected_steps.add(chosen)
        because.append({"need_state": str(s), "produced_by": str(chosen)})

        for pre in steps_view[chosen].preconditions:
            if pre.type == KSType.STATE:
                solve_state(pre)

    for s in list(needed_states):
        solve_state(s)

    ordered = sorted(selected_steps, key=lambda sid: kb.lot_index(proc_id, sid))
    return ordered, {"because_chain": because, "target_states": [str(s) for s in target_states]}
