"""
Contains the implementation of SolObject class for the interpreter.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from int.src.interpreter.runtime.sol_class import SolClass


class SolObject:
    """Represents an instance of a class during interpretation."""

    def __init__(self, sol_class: SolClass) -> None:
        """Initialize a new instance of a class."""
        self.sol_class: SolClass = sol_class
        self.instance_attrs: dict[str, SolObject] = {}

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        return f"<{self.sol_class.name} instance>"
