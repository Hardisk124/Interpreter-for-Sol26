"""
Built-in methods for the SOL26 Block class.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from int.src.interpreter.builtins.helper_methods import _require_block, _sol_bool, _value_selector
from int.src.interpreter.error_codes import ErrorCode
from int.src.interpreter.exceptions import InterpreterError
from int.src.interpreter.runtime import SolObject

if TYPE_CHECKING:
    from int.src.interpreter.builtins import BlockEvaluator, BuiltinFn
    from int.src.interpreter.class_registry import ClassRegistry

def _block_is_block(receiver: SolObject, args: list[SolObject],
              registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """returns true for Block."""
    return _sol_bool(True)

def _block_value(receiver: SolObject, args: list[SolObject],
             registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Evaluates the block with the given arguments and returns the result."""
    block = _require_block(receiver, "Block value")
    expected_arity = _value_selector(block.arity)
    actual_selector = _value_selector(len(args))
    if expected_arity != actual_selector:
        raise InterpreterError(
            ErrorCode.INT_DNU,
            f"Block expected selector '{expected_arity}' but got '{actual_selector}'",
        )
    return eval_block(block, args)

def _block_while_true(receiver: SolObject, args: list[SolObject],
             registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Evaluates the block repeatedly while the condition block evaluates to true.
    -Evaluate the receiver block (condition) — must be zero-arity.
    -If result is TRUE, evaluate bodyBlock (zero-arity).
    -If result is FALSE (or not boolean), stop.
    Returns the result of the last body evaluation, or nil if never run.
    """
    from int.src.interpreter.class_registry import nil, true
    condition_block = _require_block(receiver, "Block whileTrue:")
    body_block = _require_block(args[0], "Block whileTrue Body:")

    result: SolObject = nil
    while True:
        condition_result = eval_block(condition_block, [])
        if condition_result is not true:
            break

        result = eval_block(body_block, [])

    return result


METHODS: dict[str, BuiltinFn] = {
    "whileTrue:": _block_while_true,
    "isBlock":    _block_is_block,
}
