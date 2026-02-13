# src/core/rules/drels.py

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from core.ks.types import KSId
from core.runtime.world import Context, WorldState

class DRelEffectType(str, Enum):
    INJECT_STEP_PRECONDITION = "INJECT_STEP_PRECONDITION"
    INJECT_STEP_TOOL = "INJECT_STEP_TOOL"
    ADD_VALIDATOR = "ADD_VALIDATOR"

@dataclass
class DRel:
    id: str
    description: str
    target_step: Optional[KSId] = None
    target_procedure: Optional[KSId] = None
    condition: Callable[[Context, WorldState], bool] = lambda ctx, w: False
    effect_type: DRelEffectType = DRelEffectType.INJECT_STEP_PRECONDITION
    payload: Any = None
