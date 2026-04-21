"""
Contains the implementation of the Block object for the interpreter.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from interpreter.enviroment import Enviroment
from interpreter.input_model import Block
from interpreter.runtime.sol_class import SolClass
from interpreter.runtime.sol_object import SolObject


class SolBlock(SolObject):
    """Represents a block object"""

    def __init__(self, sol_class: SolClass, ast_block: Block,
        captured_env: Enviroment, self_obj: SolObject | None = None,
        super_class: SolClass | None = None) -> None:
        """Initialize a new instance of SolBlock."""
        super().__init__(sol_class)
        self.ast_block: Block = ast_block
        self.captured_env: Enviroment = captured_env
        self.self_obj: SolObject | None = self_obj
        self.super_class: SolClass | None = super_class

    @property
    def arity(self) -> int:
        """Return the number of parameters the block expects."""
        return self.ast_block.arity

    def __repr__(self) -> str:
        """Return a string representation of the Block object."""
        return f"<Block arity={self.arity}>"
