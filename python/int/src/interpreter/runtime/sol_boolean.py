"""
Contains the implementation of the SolBoolean class, which represents
a boolean object in the interpreter.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from interpreter.runtime.sol_object import SolObject


class SolBoolean(SolObject):
    """Represents a boolean object."""

    def __repr__(self) -> str:
        """Return a string representation of the boolean object."""
        return f"<{self.sol_class.name}>"
