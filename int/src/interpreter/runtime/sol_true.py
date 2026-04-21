"""
Contains the implementation of the SolTrue class, which represents the True object.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from int.src.interpreter.runtime.sol_boolean import SolBoolean
from int.src.interpreter.runtime.sol_class import SolClass


class SolTrue(SolBoolean):
    """Represents the True object"""

    _instatence: SolTrue | None = None

    def __new__(cls, sol_class: SolClass) -> SolTrue:
        """Create a singleton instance of SolTrue"""
        if cls is SolTrue:
            if SolTrue._instatence is None:
                SolTrue._instatence = super().__new__(cls)
            return SolTrue._instatence
        return super().__new__(cls)

    def __repr__(self) -> str:
        """Return a string representation of the True object."""
        return "<true>"
