"""Declarative validation registry and runner."""

from .model import GateResult, GateSpec
from .registry import load_registry, select_gates

__all__ = ["GateResult", "GateSpec", "load_registry", "select_gates"]
