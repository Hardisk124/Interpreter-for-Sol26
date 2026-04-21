"""
Helper methods for built-in methods in SOL26.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.runtime import SolBlock, SolBoolean, SolInteger, SolObject, SolString


def _require_integer(obj: SolObject, method_name: str) -> SolInteger:
    """Asserts that the given object is a SolInteger. Raises error 52 otherwise."""
    if not isinstance(obj, SolInteger):
        raise InterpreterError(
            ErrorCode.INT_OTHER,
            f"Method '{method_name}' requires an Integer argument, got {obj}",
        )
    return obj

def _require_string(obj: SolObject, method_name: str) -> SolString:
    """Asserts that the given object is a SolString. Raises error 52 otherwise."""
    if not isinstance(obj, SolString):
        raise InterpreterError(
            ErrorCode.INT_OTHER,
            f"Method '{method_name}' requires a String argument, got {obj}",
        )
    return obj

def _require_block(obj: SolObject, method_name: str) -> SolBlock:
    """Asserts that the given object is a SolBlock. Raises error 51 otherwise."""
    if not isinstance(obj, SolBlock):
        raise InterpreterError(
            ErrorCode.INT_OTHER,
            f"Method '{method_name}' requires a Block argument, got {obj}",
        )
    return obj

def _sol_bool(value: bool) -> SolObject:
    """Converts a Python bool to Sol bool."""
    from interpreter.class_registry import false, true
    return true if value else false

def _value_selector(arity: int) -> str:
    """Generate the Block value selector for a given arity."""
    if arity == 0:
        return "value"
    return "value:" * arity

def _require_boolean(obj: SolObject, method_name: str) -> SolBoolean:
    """Asserts that the given object is a SolBoolean. Raises error 52 otherwise."""
    if not isinstance(obj, SolBoolean):
        raise InterpreterError(
            ErrorCode.INT_OTHER,
            f"Method '{method_name}' requires a Boolean argument, got {obj}",
        )
    return obj

def _is_value_selector(selector: str) -> bool:
    """Return True if selector is 'value' or 'value:value:...' pattern."""
    if selector == "value":
        return True
    if not selector.endswith(":"):
        return False
    parts = selector.split(":")
    return all(p == "value" for p in parts[:-1]) and parts[-1] == ""
