# src/core/ks/types.py

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class KSType(str, Enum):
    CLOUD = "CLOUD"
    PROCEDURE = "PROCEDURE"
    STEP = "STEP"
    COMPONENT = "COMPONENT"
    STATE = "STATE"
    EVIDENCE_SEGMENT = "EVIDENCE_SEGMENT"
    TOOL = "TOOL"

@dataclass(frozen=True)
class KSId:
    type: KSType
    name: str
    def __str__(self) -> str:
        return f"{self.type.value}:{self.name}"

class ActionType(str, Enum):
    ENSURE_OFF = "ENSURE_OFF"
    PRESS_BUTTON = "PRESS_BUTTON"
    OPEN_COVER = "OPEN_COVER"
    REMOVE_COMPONENT = "REMOVE_COMPONENT"
    CLEAN_COMPONENT = "CLEAN_COMPONENT"
    WIPE_DRY = "WIPE_DRY"
    REINSTALL_COMPONENT = "REINSTALL_COMPONENT"
    CLOSE_COVER = "CLOSE_COVER"
    CLEAN_AREA = "CLEAN_AREA"
    REINSTALL_MULTIPLE = "REINSTALL_MULTIPLE"
    FINISH = "FINISH"
    UNKNOWN = "UNKNOWN"
