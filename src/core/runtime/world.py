# src/core/runtime/world.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Set

from core.ks.types import KSId

@dataclass
class Context:
    mode: str = "maintenance"   # maintenance | production
    machine_variant: str = "default"
    available_tools: Set[KSId] = field(default_factory=set)

@dataclass
class WorldState:
    states: Set[KSId] = field(default_factory=set)
    slots: Dict[str, Any] = field(default_factory=dict)

    def has(self, s: KSId) -> bool:
        return s in self.states

    def add(self, s: KSId) -> None:
        self.states.add(s)

    def remove(self, s: KSId) -> None:
        if s in self.states:
            self.states.remove(s)
