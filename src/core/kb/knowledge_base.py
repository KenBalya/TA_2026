# src/core/kb/knowledge_base.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ks.types import KSId, KSType, ActionType
from core.ks.entities import Cloud, Component, EvidenceSegment, Procedure, State, Step, Tool, Validator, EffectFn
from core.utils.text import norm_text, tokenize
from core.rules.drels import DRel

@dataclass
class Candidate:
    id: KSId
    score: float
    matched_alias: str

class KnowledgeBase:
    def __init__(self) -> None:
        self.clouds: Dict[KSId, Cloud] = {}
        self.procedures: Dict[KSId, Procedure] = {}
        self.steps: Dict[KSId, Step] = {}
        self.components: Dict[KSId, Component] = {}
        self.tools: Dict[KSId, Tool] = {}
        self.states: Dict[KSId, State] = {}
        self.segments: Dict[KSId, EvidenceSegment] = {}
        self.drels: List[DRel] = []

        self._component_alias_index: Dict[str, Set[KSId]] = {}
        self._tool_alias_index: Dict[str, Set[KSId]] = {}

    def add_component(self, name: str, label: str, aliases: List[str]) -> KSId:
        cid = KSId(KSType.COMPONENT, name)
        comp = Component(id=cid, label=label, aliases=set(map(norm_text, aliases + [label, name])))
        self.components[cid] = comp
        for a in comp.aliases:
            self._component_alias_index.setdefault(a, set()).add(cid)
        return cid

    def add_tool(self, name: str, label: str, aliases: List[str]) -> KSId:
        tid = KSId(KSType.TOOL, name)
        tool = Tool(id=tid, label=label, aliases=set(map(norm_text, aliases + [label, name])))
        self.tools[tid] = tool
        for a in tool.aliases:
            self._tool_alias_index.setdefault(a, set()).add(tid)
        return tid

    def add_state(self, name: str, label: str) -> KSId:
        sid = KSId(KSType.STATE, name)
        self.states[sid] = State(id=sid, label=label)
        return sid

    def add_segment(self, video_id: str, seg: Dict[str, Any]) -> KSId:
        sid = KSId(KSType.EVIDENCE_SEGMENT, f"{video_id}:seg{seg['segment_id']}")
        self.segments[sid] = EvidenceSegment(
            id=sid,
            video_id=video_id,
            segment_id=int(seg["segment_id"]),
            start_time=seg["start_time"],
            end_time=seg["end_time"],
            caption=seg.get("caption", "") or "",
            speech=seg.get("speech_content", "") or "",
        )
        return sid

    def add_procedure(self, video_id: str, title: str, summary: str) -> KSId:
        pid = KSId(KSType.PROCEDURE, video_id)
        self.procedures[pid] = Procedure(id=pid, video_id=video_id, title=title, summary=summary, lot=[])
        return pid

    def add_step(
        self,
        procedure_id: KSId,
        index: int,
        title: str,
        action: ActionType,
        target_components: List[KSId],
        pre: List[KSId],
        post: List[KSId],
        tools: List[KSId],
        evidence: List[KSId],
        notes: str = "",
        validators: Optional[List[Validator]] = None,
        effects: Optional[List[EffectFn]] = None,
    ) -> KSId:
        sid = KSId(KSType.STEP, f"{procedure_id.name}:step{index}")
        self.steps[sid] = Step(
            id=sid,
            procedure_id=procedure_id,
            index=index,
            title=title,
            action_type=action,
            target_components=list(target_components),
            preconditions=list(pre),
            postconditions=list(post),
            tools=list(tools),
            evidence_segments=list(evidence),
            notes=notes,
            validators=list(validators or []),
            effects=list(effects or []),
        )
        self.procedures[procedure_id].lot.append(sid) 
        return sid

    def add_cloud(self, name: str, label: str, procedure_ids: List[KSId]) -> KSId:
        cid = KSId(KSType.CLOUD, name)
        self.clouds[cid] = Cloud(id=cid, label=label, procedure_ids=list(procedure_ids))
        return cid

    def add_drel(self, drel: DRel) -> None:
        self.drels.append(drel)


    def resolve_component_candidates(self, mention: str, scope_proc: Optional[KSId] = None) -> List[Candidate]:
        m = norm_text(mention)
        cands: Dict[KSId, Candidate] = {}

        aliases = sorted(self._component_alias_index.keys(), key=len, reverse=True)
        for a in aliases:
            if a and (a == m or a in m):
                for cid in self._component_alias_index[a]:
                    score = 2.0 + min(len(a) / 10.0, 3.0)
                    if scope_proc:
                        for sid in self.procedures[scope_proc].lot:
                            if cid in self.steps[sid].target_components:
                                score += 1.5
                                break
                    prev = cands.get(cid)
                    if prev is None or score > prev.score:
                        cands[cid] = Candidate(id=cid, score=score, matched_alias=a)

        if not cands:
            mtok = set(tokenize(m))
            for cid, comp in self.components.items():
                ctok = set(tokenize(comp.label))
                ov = len(mtok & ctok)
                if ov:
                    cands[cid] = Candidate(id=cid, score=0.5 + ov, matched_alias="token_overlap")

        return sorted(cands.values(), key=lambda x: x.score, reverse=True)

    def resolve_tool_candidates(self, mention: str, scope_proc: Optional[KSId] = None) -> List[Candidate]:
        m = norm_text(mention)
        cands: Dict[KSId, Candidate] = {}

        aliases = sorted(self._tool_alias_index.keys(), key=len, reverse=True)
        for a in aliases:
            if a and (a == m or a in m):
                for tid in self._tool_alias_index[a]:
                    score = 2.0 + min(len(a) / 10.0, 3.0)
                    if scope_proc:
                        for sid in self.procedures[scope_proc].lot:
                            if tid in self.steps[sid].tools:
                                score += 1.5
                                break
                    prev = cands.get(tid)
                    if prev is None or score > prev.score:
                        cands[tid] = Candidate(id=tid, score=score, matched_alias=a)

        if not cands:
            mtok = set(tokenize(m))
            for tid, tool in self.tools.items():
                ttok = set(tokenize(tool.label))
                ov = len(mtok & ttok)
                if ov:
                    cands[tid] = Candidate(id=tid, score=0.5 + ov, matched_alias="token_overlap")

        return sorted(cands.values(), key=lambda x: x.score, reverse=True)

    def procedure_by_hint(self, hint: str) -> Optional[KSId]:
        h = norm_text(hint)
        best: Tuple[float, Optional[KSId]] = (0.0, None)
        for pid, p in self.procedures.items():
            blob = norm_text(p.title + " " + p.summary)
            score = 0.0
            if h and h in blob:
                score += 3.0
            ht = set(tokenize(h))
            bt = set(tokenize(blob))
            score += 0.2 * len(ht & bt)
            if score > best[0]:
                best = (score, pid)
        return best[1]

    def lot_index(self, procedure_id: KSId, step_id: KSId) -> int:
        lot = self.procedures[procedure_id].lot
        for i, sid in enumerate(lot):
            if sid == step_id:
                return i
        return -1

    def find_step_by_anchor(self, procedure_id: KSId, anchor_verb: str, anchor_obj: str) -> Optional[KSId]:
        v = norm_text(anchor_verb or "")
        o = norm_text(anchor_obj or "")

        comps = self.resolve_component_candidates(o, scope_proc=procedure_id) if o else []
        comp_best = comps[0].id if comps else None

        best: Tuple[float, Optional[KSId]] = (0.0, None)
        for sid in self.procedures[procedure_id].lot:
            st = self.steps[sid]
            blob = norm_text(st.title + " " + st.notes)
            score = 0.0

            if v and v in blob:
                score += 2.0
            if o and o in blob:
                score += 2.0
            if comp_best and comp_best in st.target_components:
                score += 2.5

            # action-type heuristic (bahasa Indo -> action type)
            if v in {"melepas", "lepas", "remove"} and st.action_type == ActionType.REMOVE_COMPONENT:
                score += 1.5
            if v in {"buka", "dibuka", "open"} and st.action_type == ActionType.OPEN_COVER:
                score += 1.5
            if v in {"memasang", "pasang", "reinstall", "install"} and st.action_type in {ActionType.REINSTALL_COMPONENT, ActionType.REINSTALL_MULTIPLE}:
                score += 1.5

            if score > best[0]:
                best = (score, sid)

        return best[1]
