"""
Contains the implementation of the Nil object for the interpreter.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from typing import ClassVar

from interpreter.runtime.sol_class import SolClass
from interpreter.runtime.sol_object import SolObject


class SolNil(SolObject):
    """Represents the Nil object"""

    _instatence: ClassVar[SolNil | None] = None

    def __new__(cls, sol_class: SolClass) -> SolNil:
        """Create a singleton instance of SolNil"""
        if cls is SolNil:
            instance = cls._instatence
            if instance is None:
                instance = super().__new__(cls)
                cls._instatence = instance
            return instance
        return super().__new__(cls)

    def __repr__(self) -> str:
        """Return a string representation of the Nil object."""
        return "<nil>"
