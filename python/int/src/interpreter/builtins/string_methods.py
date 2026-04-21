"""
Built-in methods for the SOL26 String class.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from interpreter.builtins.helper_methods import _require_string, _sol_bool
from interpreter.runtime import SolInteger, SolObject, SolString

if TYPE_CHECKING:
    from interpreter.builtins import BlockEvaluator, BuiltinFn
    from interpreter.class_registry import ClassRegistry





def _str_print(receiver: SolObject, args: list[SolObject],
           registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Prints the string to standard output and returns self."""
    receiver = _require_string(receiver, "String print")
    print(receiver.internal_value, end="")
    return receiver

def _str_equal_to(receiver: SolObject, args: list[SolObject],
             registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns true if the receiver and the argument are equal."""
    other = _require_string(args[0], "String equalTo")
    receiver = _require_string(receiver, "String equalTo")
    return _sol_bool(receiver.internal_value == other.internal_value)

def _str_as_string(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns self."""
    return receiver

def _str_as_integer(receiver: SolObject, args: list[SolObject],
                registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns the integer representation of the string, or nil if invalid."""
    from interpreter.class_registry import nil
    receiver = _require_string(receiver, "String asInteger")
    try:
        return SolInteger(registry.get_class("Integer"), int(receiver.internal_value))
    except ValueError:
        return nil

def _str_concatenate_with(receiver: SolObject, args: list[SolObject],
                registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns a new string that is the concatenation of the receiver and the argument.
    Else return nil if the argument is not a string.
    """
    from interpreter.class_registry import nil
    receiver = _require_string(receiver, "String concatenateWith")
    if not isinstance(args[0], SolString):
        return nil
    result = receiver.internal_value + args[0].internal_value
    return SolString(registry.get_class("String"), result)


def _str_starts_with_ends_before(receiver: SolObject, args: list[SolObject],
                registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    startsWith: start endsBefore: stop

    Returns substring from index `start` (1-based) up to but not including
    `stop`.  Returns nil if arguments are not positive integers.
    Returns empty string if stop - start <= 0.
    If stop > length, returns substring to end of string.
    """
    from interpreter.class_registry import nil
    receiver = _require_string(receiver, "String startsWith:endsBefore:")

    if not isinstance(args[0], SolInteger) or not isinstance(args[1], SolInteger):
        return nil

    start = args[0].internal_value
    stop = args[1].internal_value

    if start <= 0 or stop <= 0:
        return nil
    if stop - start <= 0:
        return SolString(registry.get_class("String"), "")

    # Convert python indexes
    start_idx = start - 1
    stop_idx = stop - 1
    substring = receiver.internal_value[start_idx:stop_idx]
    return SolString(registry.get_class("String"), substring)

def _str_length(receiver: SolObject, args: list[SolObject],
                registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns the length of the string."""
    receiver = _require_string(receiver, "String length")
    return SolInteger(registry.get_class("Integer"), len(receiver.internal_value))

def _str_is_string(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """returns true for String."""
    return _sol_bool(True)


def _str_read(receiver: SolObject, args: list[SolObject],
            registry: ClassRegistry, eval_block: BlockEvaluator,) -> SolObject:
    """
    String read  (class-side method, but called like an instance method here)
    Reads one line from stdin and returns it as a string.
    The input_io stream is injected via the registry at interpreter startup.
    """
    input_io = getattr(registry, "_input_io", None)
    line = sys.stdin.readline() if input_io is None else input_io.readline()
    if line.endswith("\n"):
        line = line[:-1]
    return SolString(registry.get_class("String"), line)

METHODS: dict[str, BuiltinFn] = {
    "print":                  _str_print,
    "equalTo:":               _str_equal_to,
    "asString":               _str_as_string,
    "asInteger":              _str_as_integer,
    "concatenateWith:":       _str_concatenate_with,
    "startsWith:endsBefore:": _str_starts_with_ends_before,
    "length":                 _str_length,
    "isString":               _str_is_string,
    "read":                   _str_read,
}
