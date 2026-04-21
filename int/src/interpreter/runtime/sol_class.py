"""
Contains the implementation of the SolClass class for the interpreter,
the main class for representing classes in the runtime.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from dataclasses import dataclass, field

from int.src.interpreter.input_model import Block


@dataclass
class SolClass:
    """Represents a class during interpretation."""

    name: str
    parent: SolClass | None = None
    methods: dict[str, Block] = field(default_factory=dict)
