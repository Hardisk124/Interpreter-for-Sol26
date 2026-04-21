"""
Built-in methods for the SOL26 True and False classes.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from interpreter.builtins.helper_methods import _require_block, _require_boolean, _sol_bool
from interpreter.runtime import SolObject, SolString

if TYPE_CHECKING:
    from interpreter.builtins import BlockEvaluator, BuiltinFn
    from interpreter.class_registry import ClassRegistry

def _bool_as_string(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns 'true' for True and 'false' for False."""
    from interpreter.class_registry import true
    receiver = _require_boolean(receiver, "Boolean asString")
    text = "true" if receiver is true else "false"
    return SolString(registry.get_class("String"), text)

def _bool_is_boolean(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """returns true for True and False."""
    return _sol_bool(True)

def _true_not(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Negation of true, returns false."""
    return _sol_bool(False)

def _false_not(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Negation of false, returns true."""
    return _sol_bool(True)

def _true_and(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Logical AND for true. Evaluates the argument block and returns its result."""
    block = _require_block(args[0], "True and:")
    return eval_block(block, [])

def _false_and(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Logical AND for false. Does not evaluate the argument block and returns false."""
    return _sol_bool(False)

def _true_or(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Logical OR for true. Does not evaluate the argument block and returns true."""
    return _sol_bool(True)

def _false_or(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Logical OR for false. Evaluates the argument block and returns its result."""
    block = _require_block(args[0], "False or:")
    return eval_block(block, [])

def _true_if_true_if_false(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Evaluates the first block argument (ifTrue) and returns its result."""
    trueblock = _require_block(args[0], "True ifTrue:ifFalse: trueBlock")
    return eval_block(trueblock, [])

def _false_if_true_if_false(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """Evaluates the second block argument (ifFalse) and returns its result."""
    falseblock = _require_block(args[1], "False ifTrue:ifFalse: falseBlock")
    return eval_block(falseblock, [])

TRUE_METHODS: dict[str, BuiltinFn] = {
    "asString":        _bool_as_string,
    "isBoolean":       _bool_is_boolean,
    "not":             _true_not,
    "and:":            _true_and,
    "or:":             _true_or,
    "ifTrue:ifFalse:": _true_if_true_if_false,
}

FALSE_METHODS: dict[str, BuiltinFn] = {
    "asString":        _bool_as_string,
    "isBoolean":       _bool_is_boolean,
    "not":             _false_not,
    "and:":            _false_and,
    "or:":             _false_or,
    "ifTrue:ifFalse:": _false_if_true_if_false,
}
