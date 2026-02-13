# src/core/query/ir.py

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.ks.types import KSId
from core.runtime.world import Context

class IntentType(str, Enum):
    PRECONDITION = "PRECONDITION"
    HOW_TO = "HOW_TO"
    WHERE = "WHERE"
    NEXT_STEP = "NEXT_STEP"
    UNKNOWN = "UNKNOWN"

class QuestionFocus(str, Enum):
    COMPONENT_TO_OPEN = "COMPONENT_TO_OPEN"
    STEPS = "STEPS"
    EVIDENCE = "EVIDENCE"
    UNKNOWN = "UNKNOWN"

@dataclass
class QueryIR1:
    intent: IntentType
    procedure_hint: Optional[str] = None
    anchor_verb: Optional[str] = None
    anchor_object: Optional[str] = None
    temporal_relation: Optional[str] = None
    focus: QuestionFocus = QuestionFocus.UNKNOWN
    target_token: Optional[str] = None

@dataclass
class QueryIR2:
    intent: IntentType
    cloud_id: KSId
    procedure_id: KSId
    anchor_step_id: Optional[KSId] = None
    temporal_relation: Optional[str] = None
    focus: QuestionFocus = QuestionFocus.UNKNOWN
    target_entity: Optional[KSId] = None
    ctx: Context = field(default_factory=Context)

@dataclass
class AnswerBundle:
    intent: IntentType
    procedure_title: str
    items: List[Dict[str, Any]]
    trace: Dict[str, Any] = field(default_factory=dict)
