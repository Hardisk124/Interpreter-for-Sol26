"""
Built-in methods for the SOL26 Nil class.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from interpreter.builtins.helper_methods import _sol_bool
from interpreter.runtime import SolObject, SolString

if TYPE_CHECKING:
    from interpreter.builtins import BlockEvaluator, BuiltinFn
    from interpreter.class_registry import ClassRegistry


def _nil_as_string(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns 'nil' for Nil."""
    return SolString(registry.get_class("String"), "nil")

def _nil_is_nil(receiver: SolObject, args: list[SolObject],
             registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns true for Nil."""
    return _sol_bool(True)

METHODS: dict[str, BuiltinFn] = {
    "asString": _nil_as_string,
    "isNil": _nil_is_nil,
}
