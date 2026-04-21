"""
This module creates and manages the ClassRegistry — a central store of all
SOL26 classes (both built-in and user-defined) available during interpretation.

Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Block, ClassDef
from interpreter.runtime import (
    SolBlock,
    SolClass,
    SolFalse,
    SolInteger,
    SolNil,
    SolObject,
    SolString,
    SolTrue,
)

# Built in SolClass objects
object_class = SolClass(name="Object", parent=None)
nil_class = SolClass(name="Nil", parent=object_class)
true_class = SolClass(name="True", parent=object_class)
false_class = SolClass(name="False", parent=object_class)
integer_class = SolClass(name="Integer", parent=object_class)
string_class = SolClass(name="String", parent=object_class)
block_class = SolClass(name="Block", parent=object_class)

# singletons
nil: SolNil = SolNil(nil_class)
true: SolTrue = SolTrue(true_class)
false: SolFalse = SolFalse(false_class)


class ClassRegistry:
    """Central registry of all SOL26 classes available during interpretation.
    Attributes
    ----------
    _classes : dict[str, SolClass]
        Maps class name → SolClass instance.
    """

    def __init__(self) -> None:
        """Initialize the registry"""
        self.classes: dict[str, SolClass] = {}
        self._input_io: object | None = None
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Populates the registry with the built-in classes."""
        for cls in [
            object_class,
            nil_class,
            true_class,
            false_class,
            integer_class,
            string_class,
            block_class,
        ]:
            self.classes[cls.name] = cls

    def register_program(self, class_defs: list[ClassDef]) -> None:
        """Register all user-defined classes from the parsed XML program.
        Parameters
        ----------
        class_defs:
            The list of ClassDef objects produced by parsing the XML input.
        Raises
        ------
        InterpreterError(SEM_ERROR)   — class redefinition (error 35)
        InterpreterError(SEM_UNDEF)   — unknown parent class (error 32)
        """

        # for solclass, parentmane as string because we dont know it yet,
        # we will resolve it in the second pass
        new_classes: dict[str, tuple[SolClass, str]] = {}
        for class_def in class_defs:
            name = class_def.name

            if name in self.classes or name in new_classes:
                raise InterpreterError(ErrorCode.SEM_ERROR, f"Class '{name}' is already defined")

            sol_class = SolClass(name=name)  # parent will be resolved later

            for method in class_def.methods:
                sol_class.methods[method.selector] = method.block

            new_classes[name] = (sol_class, class_def.parent)

        # resolve parents
        for name, (sol_class, parent_name) in new_classes.items():
            parent = self._resoleve_parent(parent_name, new_classes)
            sol_class.parent = parent
            self.classes[name] = sol_class

    def _resoleve_parent(
        self, parent_name: str, pending: dict[str, tuple[SolClass, str]]
    ) -> SolClass:
        """Helper method to resolve the parent class by name,
        checking both the already registered classes and the pending ones.
        """
        if parent_name in self.classes:
            return self.classes[parent_name]
        if parent_name in pending:
            parent_sol_class, _ = pending[parent_name]
            return parent_sol_class
        raise InterpreterError(ErrorCode.SEM_UNDEF, f"Unknown parent class '{parent_name}'")

    def get_class(self, name: str) -> SolClass:
        """Return SolClass for given name, or raise error 32 if not found."""
        if name in self.classes:
            return self.classes[name]
        raise InterpreterError(ErrorCode.SEM_UNDEF, f"Class '{name}' is not defined")

    def is_registered(self, name: str) -> bool:
        """Returns True if a class with the given name is registered."""
        return name in self.classes

    def create_instance(self, sol_class: SolClass) -> SolObject:
        """Creates a new instance of the given SolClass.
         Parameters
        ----------
        sol_class:
            The class to instantiate.
        Returns
        -------
        A fresh SolObject (or the singleton for Nil/True/False).
        """
        name = sol_class.name
        if name == "Nil":
            return nil
        if name == "True":
            return true
        if name == "False":
            return false
        if name == "Integer":
            return SolInteger(sol_class, 0)
        if name == "String":
            return SolString(sol_class, "")
        if name == "Block":
            from interpreter.enviroment import Enviroment
            from interpreter.input_model import Block as AstBlock  # to avoid circular imports
            empty_ast = AstBlock(arity=0)
            return SolBlock(sol_class, empty_ast, Enviroment())

        return SolObject(sol_class)

    def create_instance_from(self, sol_class: SolClass, source: SolObject) -> SolObject:
        """Create an instance using the `from:` constructor.
         Parameters
        ----------
        sol_class:
            The class whose `from:` class method was called.
        source:
            The object whose state is copied.
        Raises
        ------
        InterpreterError(INT_INVALID_ARG) — incompatible source (error 53)
        """

        name = sol_class.name
        if name == "Nil":
            return nil
        if name == "True":
            return true
        if name == "False":
            return false

        if self.inherits_from(sol_class, "Integer"):
            if not isinstance(source, SolInteger):
                raise InterpreterError(
                    ErrorCode.INT_INVALID_ARG,
                    f"'from:' for class '{name}' requires an Integer source",
                )
            new_obj: SolObject = SolInteger(sol_class, source.internal_value)
            new_obj.instance_attrs = dict(source.instance_attrs)  # copy instance attributes
            return new_obj

        if self.inherits_from(sol_class, "String"):
            if not isinstance(source, SolString):
                raise InterpreterError(
                    ErrorCode.INT_INVALID_ARG,
                    f"'from:' for class '{name}' requires a String source",
                )
            new_obj = SolString(sol_class, source.internal_value)
            new_obj.instance_attrs = dict(source.instance_attrs)  # copy instance attributes
            return new_obj

        new_obj = SolObject(sol_class)
        new_obj.instance_attrs = dict(source.instance_attrs)  # copy instance attributes
        return new_obj

    def inherits_from(self, sol_class: SolClass, ancestor_name: str) -> bool:
        """Return True if sol_class is or inherits from the named class."""
        current: SolClass | None = sol_class
        while current is not None:
            if current.name == ancestor_name:
                return True
            current = current.parent
        return False

    def find_method(self, sol_class: SolClass, selector: str) -> tuple[SolClass, Block] | None:
        """Find the user-defined method in class and its parents
        Returns
        -------
        (defining_class, Block) if found, or None if not found anywhere.
        The defining_class is needed for `super` dispatch.
        """
        current: SolClass | None = sol_class
        while current is not None:
            if selector in current.methods:
                return (current, current.methods[selector])
            current = current.parent
        return None

    def find_method_from(self, start_class: SolClass,
                        selector: str) -> tuple[SolClass, Block] | None:
        """Like find_method but starts searching from start_class's parent.
        This implements `super` dispatch: when a method body uses `super`
        as the receiver, we skip the current class and start looking from
        its parent upward.
        """
        current: SolClass | None = start_class.parent
        while current is not None:
            if selector in current.methods:
                return (current, current.methods[selector])
            current = current.parent
        return None

    def __repr__(self) -> str:
        return f"ClassRegistry({list(self.classes.keys())})"
