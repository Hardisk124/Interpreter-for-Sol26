"""
Contains the implementation of the String class for the interpreter.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""


from int.src.interpreter.runtime.sol_class import SolClass
from int.src.interpreter.runtime.sol_object import SolObject


class SolString(SolObject):
    """Represents a String object."""

    def __init__(self, sol_class: SolClass, value: str) -> None:
        """Initialize a new instance of SolString."""
        super().__init__(sol_class)
        self.internal_value: str = value

    def __repr__(self) -> str:
        """Return a string representation of the String object."""
        return f"<String '{self.internal_value}'>"
