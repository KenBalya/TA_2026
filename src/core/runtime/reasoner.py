# src/core/runtime/reasoner.py

from __future__ import annotations
from typing import Any, Dict, List

from core.kb.knowledge_base import KnowledgeBase
from core.ks.types import KSId, KSType
from core.ks.entities import Step
from core.query.ir import AnswerBundle, IntentType, QuestionFocus, QueryIR2
from core.runtime.world import WorldState
from core.runtime.simulate import apply_drels_runtime, simulate_forward
from core.runtime.reasoning import backward_chain_minimal, producers_of_state

class Reasoner:
    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def answer(self, ir2: QueryIR2) -> AnswerBundle:
        base_world = WorldState(states=set(), slots={})
        steps_view = apply_drels_runtime(self.kb, ir2.procedure_id, ir2.ctx, base_world)
        snaps = simulate_forward(self.kb, ir2.procedure_id, steps_view, ir2.ctx, initial=base_world)

        if ir2.intent == IntentType.HOW_TO:
            return self._how_to(ir2, steps_view, snaps)
        if ir2.intent == IntentType.PRECONDITION:
            if ir2.focus == QuestionFocus.COMPONENT_TO_OPEN:
                return self._precondition_component_to_open(ir2, steps_view)
            return self._precondition_minimal(ir2, steps_view)
        if ir2.intent == IntentType.WHERE:
            return self._where(ir2, steps_view)
        if ir2.intent == IntentType.NEXT_STEP:
            return self._next_step(ir2, steps_view)
        return AnswerBundle(intent=IntentType.UNKNOWN, procedure_title=self.kb.procedures[ir2.procedure_id].title,
                            items=[{"error": "Unknown intent"}], trace={})

    def _step_to_item(self, st: Step) -> Dict[str, Any]:
        comps = [self.kb.components[c].label for c in st.target_components if c in self.kb.components]
        tools = [self.kb.tools[t].label for t in st.tools if t in self.kb.tools]
        pre = [self.kb.states[s].label for s in st.preconditions if s in self.kb.states]
        post = [self.kb.states[s].label for s in st.postconditions if s in self.kb.states]
        evidence = [self.kb.segments[eid].as_brief() for eid in st.evidence_segments]
        return {
            "step_index": st.index,
            "title": st.title,
            "action_type": st.action_type.value,
            "target_components": comps,
            "preconditions": pre,
            "postconditions": post,
            "tools": tools,
            "evidence": evidence,
        }

    def _how_to(self, ir2: QueryIR2, steps_view: Dict[KSId, Step], snaps) -> AnswerBundle:
        proc = self.kb.procedures[ir2.procedure_id]
        items = [self._step_to_item(steps_view[sid]) for sid in proc.lot]
        trace = {
            "lot": [str(x) for x in proc.lot],
            "forward_validity": [{"step": str(s.step_id), "valid": s.valid, "reasons": s.reasons} for s in snaps],
            "drels": [{"id": d.id, "desc": d.description} for d in self.kb.drels],
        }
        return AnswerBundle(intent=ir2.intent, procedure_title=proc.title, items=items, trace=trace)

    def _precondition_minimal(self, ir2: QueryIR2, steps_view: Dict[KSId, Step]) -> AnswerBundle:
        proc = self.kb.procedures[ir2.procedure_id]
        if ir2.anchor_step_id is None:
            return AnswerBundle(ir2.intent, proc.title, [{"error": "Could not resolve anchor step."}],
                                trace={"procedure_id": str(proc.id)})

        anchor = steps_view[ir2.anchor_step_id]
        needed_steps, bc_trace = backward_chain_minimal(self.kb, ir2.procedure_id, steps_view, anchor.preconditions)
        items = [self._step_to_item(steps_view[sid]) for sid in needed_steps]

        return AnswerBundle(
            intent=ir2.intent,
            procedure_title=proc.title,
            items=items,
            trace={
                "anchor_step": str(anchor.id),
                "anchor_title": anchor.title,
                "reasoning": bc_trace,
                "selected_steps": [str(s) for s in needed_steps],
            }
        )

    def _precondition_component_to_open(self, ir2: QueryIR2, steps_view: Dict[KSId, Step]) -> AnswerBundle:
        proc = self.kb.procedures[ir2.procedure_id]
        if ir2.anchor_step_id is None:
            return AnswerBundle(ir2.intent, proc.title, [{"error": "Could not resolve anchor step for removal action."}],
                                trace={"procedure_id": str(proc.id)})

        anchor = steps_view[ir2.anchor_step_id]
        needed_open_state = KSId(KSType.STATE, "GuardOpen")

        producers = producers_of_state(self.kb, ir2.procedure_id, steps_view, needed_open_state)
        producers_sorted = sorted(producers, key=lambda sid: self.kb.lot_index(ir2.procedure_id, sid))

        items: List[Dict[str, Any]] = []
        for psid in producers_sorted:
            st = steps_view[psid]
            comps = [{"id": str(cid), "label": self.kb.components[cid].label}
                     for cid in st.target_components if cid in self.kb.components]
            evidence = [self.kb.segments[eid].as_brief() for eid in st.evidence_segments]
            items.append({
                "component_to_open": comps,
                "supporting_step": {"step_id": str(st.id), "step_index": st.index, "title": st.title},
                "anchor_step": {"step_id": str(anchor.id), "step_index": anchor.index, "title": anchor.title},
                "evidence": evidence,
                "because": f"{anchor.title} requires {needed_open_state.name}, produced by {st.title}",
            })

        if not items:
            items = [{"error": "No step found that produces GuardOpen in this procedure."}]

        return AnswerBundle(
            intent=ir2.intent,
            procedure_title=proc.title,
            items=items,
            trace={
                "anchor_step": str(anchor.id),
                "needed_state": str(needed_open_state),
                "supporting_steps": [str(s) for s in producers_sorted],
            }
        )

    def _where(self, ir2: QueryIR2, steps_view: Dict[KSId, Step]) -> AnswerBundle:
        proc = self.kb.procedures[ir2.procedure_id]
        target = ir2.target_entity
        if target is None:
            return AnswerBundle(ir2.intent, proc.title, [{"error": "WHERE needs target token (e.g., Aqua Demineral, S1S)."}],
                                trace={"hint": "include target_token in IR1"})

        items: List[Dict[str, Any]] = []
        for sid in proc.lot:
            st = steps_view[sid]
            hit = False
            if target.type == KSType.TOOL and target in st.tools:
                hit = True
            if target.type == KSType.COMPONENT and target in st.target_components:
                hit = True

            if hit:
                items.append({
                    "step_index": st.index,
                    "step_title": st.title,
                    "match": str(target),
                    "tools": [self.kb.tools[t].label for t in st.tools if t in self.kb.tools],
                    "components": [self.kb.components[c].label for c in st.target_components if c in self.kb.components],
                    "evidence": [self.kb.segments[eid].as_brief() for eid in st.evidence_segments],
                })

        return AnswerBundle(ir2.intent, proc.title, items if items else [{"note": "No matching steps found."}],
                            trace={"target_entity": str(target)})

    def _next_step(self, ir2: QueryIR2, steps_view: Dict[KSId, Step]) -> AnswerBundle:
        proc = self.kb.procedures[ir2.procedure_id]
        if ir2.anchor_step_id is None:
            return AnswerBundle(ir2.intent, proc.title, [{"error": "Need anchor step for NEXT_STEP."}],
                                trace={"procedure_id": str(proc.id)})

        idx = self.kb.lot_index(ir2.procedure_id, ir2.anchor_step_id)
        if idx < 0 or idx >= len(proc.lot) - 1:
            return AnswerBundle(ir2.intent, proc.title, [{"note": "Anchor step is last; no next step."}],
                                trace={"anchor_step": str(ir2.anchor_step_id)})

        next_sid = proc.lot[idx + 1]
        st = steps_view[next_sid]
        return AnswerBundle(ir2.intent, proc.title, [self._step_to_item(st)],
                            trace={"anchor_step": str(ir2.anchor_step_id), "next_step": str(next_sid)})
