"""
Contains the implementation of the SolInteger class, which represents an integer object
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from int.src.interpreter.runtime.sol_class import SolClass
from int.src.interpreter.runtime.sol_object import SolObject


class SolInteger(SolObject):
    """Represents an Integer object."""

    def __init__(self, sol_class: SolClass, value: int) -> None:
        """Initialize a new instance of SolInteger."""
        super().__init__(sol_class)
        self.internal_value: int = value

    def __repr__(self) -> str:
        """Return a string representation of the Integer object."""
        return f"<Integer {self.internal_value}>"
