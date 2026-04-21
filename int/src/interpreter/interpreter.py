"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Martin Turčan <xturcam00@vutbr.cz>
"""

import logging
from pathlib import Path
from typing import TextIO

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from int.src.interpreter.class_registry import ClassRegistry
from int.src.interpreter.error_codes import ErrorCode
from int.src.interpreter.evaluator import send_message
from int.src.interpreter.exceptions import InterpreterError
from int.src.interpreter.input_model import ClassDef, Method, Program

logger = logging.getLogger(__name__)


class Interpreter:
    """
    The main interpreter class, responsible for loading the source file and executing the program.
    """

    def __init__(self) -> None:
        self.current_program: Program | None = None

    def load_program(self, source_file_path: Path) -> None:
        """
        Reads the source SOL-XML file and stores it as the target program for this interpreter.
        If any program was previously loaded, it is replaced by the new one.

        IPP: If you wish to run static checks on the program before execution, this is a good place
             to call them from.
        """
        logger.info("Opening source file: %s", source_file_path)
        try:
            xml_tree = etree.parse(source_file_path)
        except ParseError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_XML, message="Error parsing input XML"
            ) from e
        try:
            program = Program.from_xml_tree(xml_tree.getroot())  # type: ignore
        except ValidationError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_STRUCTURE, message="Invalid SOL-XML structure"
            ) from e

        self._validate_static_semantics(program)
        self.current_program = program

    @staticmethod
    def _selector_arity(selector: str) -> int:
        return selector.count(":")

    def _validate_method_semantics(self, class_def: ClassDef, method: Method) -> None:
        selector_arity = self._selector_arity(method.selector)
        block_arity = method.block.arity

        if selector_arity != block_arity:
            raise InterpreterError(
                error_code=ErrorCode.SEM_ARITY,
                message=(
                    f"Method '{class_def.name}>>{method.selector}' has selector arity "
                    f"{selector_arity} but block arity {block_arity}"
                ),
            )

        param_names = [param.name for param in method.block.parameters]
        if len(param_names) != len(set(param_names)):
            raise InterpreterError(
                error_code=ErrorCode.SEM_ERROR,
                message=
                f"Duplicate block parameter in method '{class_def.name}>>{method.selector}'",
            )

        for assign in method.block.assigns:
            if assign.target.name in param_names:
                raise InterpreterError(
                    error_code=ErrorCode.SEM_COLLISION,
                    message=(
                        f"Assignment to parameter '{assign.target.name}' in method "
                        f"'{class_def.name}>>{method.selector}'"
                    ),
                )

    def _validate_static_semantics(self, program: Program) -> None:
        if program.language != "SOL26":
            raise InterpreterError(
                error_code=ErrorCode.INT_STRUCTURE,
                message=f"Unsupported language: {program.language}",
            )

        for class_def in program.classes:
            seen_methods: set[str] = set()
            for method in class_def.methods:
                if method.selector in seen_methods:
                    raise InterpreterError(
                        error_code=ErrorCode.SEM_ERROR,
                        message=(
                            f"Duplicate method selector '{method.selector}' "
                            f"in class '{class_def.name}'"
                        ),
                    )
                seen_methods.add(method.selector)
                self._validate_method_semantics(class_def, method)

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.
        """
        logger.info("Executing program")

        if self.current_program is None:
            raise InterpreterError(
                error_code=ErrorCode.INT_STRUCTURE, message="No program loaded"
            )

        registry = ClassRegistry()
        registry.register_program(self.current_program.classes)
        registry._input_io = input_io

        #verify that Main class with run method exists
        main_class = None
        for class_def in self.current_program.classes:
            if class_def.name == "Main":
                main_class = class_def
                break
        if main_class is None:
            raise InterpreterError(
                error_code=ErrorCode.SEM_MAIN, message="Missing Main class")

        run_method = None
        for method in main_class.methods:
            if method.selector == "run":
                run_method = method
                break
        if run_method is None:
            raise InterpreterError(
                error_code=ErrorCode.SEM_MAIN, message="Missing Main class run method")

        if run_method.block.arity != 0:
            raise InterpreterError(
                error_code=ErrorCode.SEM_MAIN, message="Main class run method must be zero-arity")


        #create main instance and execute run method
        main_sol_class = registry.get_class("Main")
        main_instance = registry.create_instance(main_sol_class)

        #send mess to run -
        send_message(main_instance, "run", [], registry, super_class=None)


