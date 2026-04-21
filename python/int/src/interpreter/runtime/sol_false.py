"""
Contains the implementation of the False object for the interpreter.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from interpreter.runtime import SolBoolean
from interpreter.runtime.sol_class import SolClass


class SolFalse(SolBoolean):
    """Represents the False object"""

    _instatence: SolFalse | None = None

    def __new__(cls, sol_class: SolClass) -> SolFalse:
        """Create a singleton instance of SolFalse"""
        if cls is SolFalse:
            if SolFalse._instatence is None:
                SolFalse._instatence = super().__new__(cls)
            return SolFalse._instatence
        return super().__new__(cls)

    def __repr__(self) -> str:
        """Return a string representation of the False object."""
        return "<false>"
