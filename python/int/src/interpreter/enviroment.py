"""
Contains the implementation of the environment structures for the interpreter.
Author: Martin Turčan <xturcam00@fit.vutbr.cz>
"""

from __future__ import annotations

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.runtime.sol_object import SolObject


class Enviroment:
    """A single frame in the lexical scope chain.
    Each active block execution owns one Enviroment instance.  Variables
    defined by assignment statements inside that block are stored here.
    Block parameters are pre-loaded into the frame before execution starts.
    """

    def __init__(
        self, parent: Enviroment | None = None, params: dict[str, SolObject] | None = None
    ) -> None:
        """Creates a new environment frame.
        parent:
            The enclosing Enviroment (None for the outermost method block).
        params:
            Pre-initialized parameters for this frame.  Pass the dict of
            {param_name: SolObject} that come from the caller's arguments.
            These are stored as regular variables but their names are locked
            against re-assignment (error 34).
        """
        self._vars: dict[str, SolObject] = {}
        self._parent: Enviroment | None = parent
        self._params: frozenset[str] = frozenset()

        if params:
            self._vars.update(params)
            self._params = frozenset(params.keys())

    def get(self, name: str) -> SolObject:
        """Returns the value of the variable with the given name.
        If the variable is not defined in this frame, looks up the parent
        frames recursively.  Raises error 32 if the variable is not found.
        """

        frame: Enviroment | None = self
        while frame is not None:
            if name in frame._vars:
                return frame._vars[name]
            frame = frame._parent

        raise InterpreterError(ErrorCode.SEM_UNDEF, f"Undefined variable '{name}'")

    def is_defined(self, name: str) -> bool:
        """Returns True if the variable with the given name
        is defined in this frame or any parent frame.
        """
        frame: Enviroment | None = self
        while frame is not None:
            if name in frame._vars:
                return True
            frame = frame._parent
        return False

    def set(self, name: str, value: SolObject) -> None:
        """Sets the variable with the given name to the given value.
        If the variable is already defined in this frame, updates its value.
        If the variable is defined in a parent frame, updates its value there.
        If the variable is not defined in any frame, defines it in this frame.
        Raises error 34 if trying to assign to formal parameter.
        """

        frame: Enviroment | None = self
        while frame is not None:
            if name in frame._params:
                raise InterpreterError(
                    ErrorCode.SEM_COLLISION, f"Cannot assign to formal parameter '{name}'"
                )

            frame = frame._parent

        frame = self
        while frame is not None:
            if name in frame._vars:
                frame._vars[name] = value
                return
            frame = frame._parent

        # does not exist, create in current frame
        self._vars[name] = value

    def defined_names(self) -> frozenset[str]:
        """Returns all variable names reachable from this frame."""

        names: set[str] = set()
        frame: Enviroment | None = self
        while frame is not None:
            names.update(frame._vars.keys())
            frame = frame._parent
        return frozenset(names)
