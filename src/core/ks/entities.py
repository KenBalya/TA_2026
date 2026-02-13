# src/core/ks/entities.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set, Tuple, Any

from core.ks.types import KSId, KSType, ActionType
from core.utils.text import format_range
from core.runtime.world import Context, WorldState

Validator = Callable[[Context, WorldState], Tuple[bool, str]]
EffectFn  = Callable[[Context, WorldState], None]

@dataclass
class EvidenceSegment:
    id: KSId
    video_id: str
    segment_id: int
    start_time: str
    end_time: str
    caption: str
    speech: str

    def time_range(self) -> str:
        return format_range(self.start_time, self.end_time)

    def as_brief(self) -> str:
        cap = (self.caption or "").strip()
        sp = (self.speech or "").strip()
        brief = cap if cap else sp
        if len(brief) > 180:
            brief = brief[:177] + "..."
        return f"[{self.time_range()}] {brief}"

@dataclass
class Component:
    id: KSId
    label: str
    aliases: Set[str] = field(default_factory=set)

@dataclass
class Tool:
    id: KSId
    label: str
    aliases: Set[str] = field(default_factory=set)

@dataclass
class State:
    id: KSId
    label: str

@dataclass
class Step:
    id: KSId
    procedure_id: KSId
    index: int
    title: str
    action_type: ActionType

    target_components: List[KSId] = field(default_factory=list)
    preconditions: List[KSId] = field(default_factory=list)
    postconditions: List[KSId] = field(default_factory=list)
    tools: List[KSId] = field(default_factory=list)
    evidence_segments: List[KSId] = field(default_factory=list)
    notes: str = ""

    validators: List[Validator] = field(default_factory=list)
    effects: List[EffectFn] = field(default_factory=list)

    def validate(self, ctx: Context, world: WorldState) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        # declarative preconditions
        for s in self.preconditions:
            if s.type == KSType.STATE and not world.has(s):
                reasons.append(f"missing_precondition:{s.name}")

        # tool availability (only if user set available_tools)
        if ctx.available_tools:
            for t in self.tools:
                if t not in ctx.available_tools:
                    reasons.append(f"tool_unavailable:{t.name}")

        # custom validators
        for v in self.validators:
            ok, msg = v(ctx, world)
            if not ok:
                reasons.append(msg)

        return (len(reasons) == 0), reasons

    def apply(self, ctx: Context, world: WorldState) -> None:
        for s in self.postconditions:
            if s.type == KSType.STATE:
                world.add(s)
        for e in self.effects:
            e(ctx, world)

@dataclass
class Procedure:
    id: KSId
    video_id: str
    title: str
    summary: str
    lot: List[KSId] = field(default_factory=list)  # canonical LoT

@dataclass
class Cloud:
    id: KSId
    label: str
    procedure_ids: List[KSId] = field(default_factory=list)
