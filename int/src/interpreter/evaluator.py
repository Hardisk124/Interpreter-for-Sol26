"""
This file implements the core logic for the SOL26 interpreter
Contains three main functions:

  eval_expr(expr, env, self_obj, super_class, registry)
      Evaluates a single AST expression node and returns a SolObject.
      Handles: literals, variables, block literals, message sends.

  execute_block(block, args, registry)
      Executes a sequence of assignment statements inside a block.
      Returns the value of the last evaluated expression (or NIL).

  send_message(receiver, selector, args, registry, super_class)
      Dispatches a message to a receiver:
        1. Looks for a user-defined method via ClassRegistry.
        2. Falls back to built-in methods via find_builtin().
        3. Checks instance attributes (getter / setter).
        4. Raises INT_DNU (51) if nothing is found.

Author: Martin Turčan <xturcam00@vutbr.cz>
"""

from __future__ import annotations

from int.src.interpreter.builtins import find_builtin
from int.src.interpreter.class_registry import (
    ClassRegistry,
    false,
    nil,
    true,
)
from int.src.interpreter.enviroment import Enviroment
from int.src.interpreter.error_codes import ErrorCode
from int.src.interpreter.exceptions import InterpreterError
from int.src.interpreter.input_model import Block as AstBlock
from int.src.interpreter.input_model import Expr, Literal, Send
from int.src.interpreter.runtime import SolBlock, SolClass, SolInteger, SolObject, SolString


def eval_expr(expr: Expr, env: Enviroment, self_obj: SolObject | None,
              super_class: SolClass| None, registry: ClassRegistry) -> SolObject:
    """
    Evaluate one AST expression node and return the resulting SolObject.
        Parameters
    ----------
    expr : Expr
        The expression AST node (contains exactly one of: literal, var,
        block, send).
    env : Environment
        The current lexical scope for variable lookup.
    self_obj : SolObject | None
        The object bound to `self` in the current method context.
        None only at the very top level before Main is instantiated.
    super_class : SolClass | None
        The class that defined the currently executing method.
        Needed so `super` sends start searching from the right place.
    registry : ClassRegistry
        The global class registry.

    Returns
    -------
    SolObject — the value the expression evaluated to.
    """

    #literal
    if expr.literal is not None:
        return _eval_literal(expr.literal, registry)

    #variable
    if expr.var is not None:
        return _eval_var(expr.var.name, env, self_obj, registry)

    #block literal
    if expr.block is not None:
        #create SolBlock which capture the current enviroment and self - its not executed
        return SolBlock(sol_class=registry.get_class("Block"),
                        ast_block=expr.block, captured_env=env, self_obj=self_obj)

    #message send
    if expr.send is not None:
        return _eval_send(expr.send, env, self_obj, super_class, registry)

    #should never go here
    raise InterpreterError(ErrorCode.INT_STRUCTURE, "Empty expression node")


def _eval_literal(literal: Literal, registry: ClassRegistry) -> SolObject:
    """
    Helper function to evaluate a literal AST node and return the corresponding SolObject.
    """
    class_id: str = literal.class_id
    value: str = literal.value

    if class_id == "Integer":
        try:
            int_value = int(value)
        except ValueError as err:
            raise InterpreterError(ErrorCode.INT_STRUCTURE,
                                   f"Invalid integer literal: {value}") from err

        return SolInteger(registry.get_class("Integer"), value=int_value)

    if class_id == "String":
        return SolString(registry.get_class("String"), value=_escape_sequences_decoder(value))

    if class_id == "Nil" or value == "nil":
        return nil
    if class_id == "True" or value == "true":
        return true
    if class_id == "False" or value == "false":
        return false
    if class_id == "class":
        return _ClassReference(registry.get_class(value))

    raise InterpreterError(ErrorCode.INT_STRUCTURE, f"Unknown literal class_id: {class_id}")


def _escape_sequences_decoder(raw: str) -> str:
    """Decode supported escape sequences in SOL26 String literals."""
    escape_map = {
        "n": "\n",
        "\\": "\\",
        "'": "'",
    }

    out: list[str] = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            mapped = escape_map.get(nxt)
            if mapped is not None:
                out.append(mapped)
                i += 2
                continue

        out.append(ch)
        i += 1

    return "".join(out)


class _ClassReference(SolObject):
    """
    A helper class to represent a reference to a class literal (e.g., Integer, String).
    This allows us to handle messages sent to class literals (like Integer new) in a uniform way.
    """
    def __init__(self, sol_class: SolClass) -> None:
        super().__init__(sol_class)
        self.referenced_class: SolClass = sol_class

    def __repr__(self) -> str:
        """
        For debugging purposes, show the name of the referenced class.
        """
        return f"<ClassReference {self.sol_class.name}>"


def _eval_var(var_name: str, env: Enviroment, self_obj: SolObject | None,
              registry: ClassRegistry) -> SolObject:
    """
    Helper function to evaluate a variable AST node by looking it up in the lexical scope chain
    or self's instance attributes.
    """

    if var_name == "nil":
        return nil
    if var_name == "true":
        return true
    if var_name == "false":
        return false

    if var_name == "self":
        if self_obj is None:
            raise InterpreterError(ErrorCode.SEM_UNDEF,
                                   "Variable 'self' cannot be used outside of a method context")
        return self_obj

    # treat  as a value (not receiver)
    if var_name == "super":
        if self_obj is None:
            raise InterpreterError(ErrorCode.SEM_UNDEF,
                                   "Variable 'super' cannot be used outside of a method context")
        return self_obj

    if env.is_defined(var_name):
        return env.get(var_name)

    if registry.is_registered(var_name):
        return _ClassReference(registry.get_class(var_name))

    raise InterpreterError(ErrorCode.SEM_UNDEF, f"Undefined variable '{var_name}'")


def _eval_send(send: Send, env: Enviroment, self_obj: SolObject | None,
               super_class: SolClass | None, registry: ClassRegistry) -> SolObject:
    """
    Helper function to determine if receiver is super, evaluete the receiver
    expresion and arguments and dispatch the message to send_message.
    """
    selector: str = send.selector
    is_super_send = (send.receiver.var is not None and send.receiver.var.name == "super")

    #evaluate receiver
    receiver: SolObject = eval_expr(send.receiver, env, self_obj, super_class, registry)
    #evaluate arguments
    args: list[SolObject] = [eval_expr(arg.expr, env, self_obj, super_class, registry)
                             for arg in send.args]

    #where to start looking for methods
    method_start_cls: SolClass | None = None
    if is_super_send and super_class is not None:
        method_start_cls = super_class

    return send_message(receiver, selector, args, registry, method_start_cls)


def execute_block(block: SolBlock, args: list[SolObject], registry: ClassRegistry) -> SolObject:
    """
    Executes a block of assignments and returns the value of the last expression (or NIL if none).
    """

    ast_block = block.ast_block
    captured_env = block.captured_env
    self_obj = block.self_obj
    super_class = block.super_class
    # method block - params in captured env
    if len(args) == 0:
        params: dict[str, SolObject] = {}

    else:
    # closure block - arity check
        if len(args) != ast_block.arity:
            raise InterpreterError(ErrorCode.INT_DNU,
                f"Block expects {ast_block.arity} arguments, got {len(args)}")

        #map formal parameters to argument values
        params = {
            param.name: arg_val
            for param, arg_val in zip(ast_block.parameters, args, strict=True)
        }

    #new eviroment frame for the block execution, with captured env as parent
    block_env = Enviroment(parent=captured_env, params=params)

    last_val: SolObject = nil

    #evaluate ast block statements
    for assign in ast_block.assigns:
        value = eval_expr(assign.expr, block_env, self_obj, super_class, registry)

        # check for '_'
        target_name = assign.target.name
        if target_name != "_":
            block_env.set(target_name, value)

        last_val = value

    return last_val

def send_message(receiver: SolObject, selector: str, args: list[SolObject],
                 registry: ClassRegistry, super_class: SolClass | None) ->SolObject:
    """
    Dispatches a message send to the appropriate method or builtin, following the lookup rules:

    a) If receiver is a _ClassRef (a class used as message target):
       -Handle constructor class methods: new, from:, read (String only)
       -Error 32 for unknown class messages

    b) If receiver is a normal instance:
       1. Look for a user-defined method (in receiver's class chain,
          or from super_class.parent if this is a super send)
       2. Fall back to built-in methods
       3. Handle instance attribute access (getter / setter)
       4. Error 51 if nothing found
    """

    #a) Handle class literal messages
    if isinstance(receiver, _ClassReference):
        return _handle_class_mess(receiver.referenced_class, selector, args, registry)

    #b) Normal instance message send
    #determine where to start looking for methods
    if super_class is not None:
        result = registry.find_method_from(super_class, selector)
    else:
        result = registry.find_method(receiver.sol_class, selector)

    if result is not None:
        defining_cls, method_block = result
        return _invoke_user_method(receiver, method_block, defining_cls, args, registry)

    #try built-in methods
    start_class_name = (super_class.parent.name
                        if super_class is not None and super_class.parent is not None
                        else receiver.sol_class.name)
    builtin_func = find_builtin(start_class_name, selector, registry)
    if builtin_func is not None:
        #callback hack - dont want to make circular imports
        def eval_block_callback(block: SolBlock, block_args: list[SolObject]) -> SolObject:
            return execute_block(block, block_args, registry)

        return builtin_func(receiver, args, registry, eval_block_callback)

    #try instance attribute getter / setter
    attr_result = _handle_instance_attr(receiver, selector, args, registry, super_class)
    if attr_result is not None:
        return attr_result

    #nothing found
    raise InterpreterError(ErrorCode.INT_DNU,
    f"Receiver of class '{receiver.sol_class.name}' does not understand message '{selector}'")


def _handle_class_mess(sol_class: SolClass, selector: str, args: list[SolObject],
                       registry: ClassRegistry) -> SolObject:
    """Handle messages sent to class - construktor calls
    3 supported messages:
    new - creates a default instance
    from: - creates an instance copying from another object
    read - reads a line from stdin
    other - error 32
    """

    if selector == "new":
        return registry.create_instance(sol_class)

    if selector == "from:":
        if len(args) != 1:
            raise InterpreterError(ErrorCode.INT_DNU,
                                f"Message 'from:' expects exactly 1 argument but got {len(args)}")
        return registry.create_instance_from(sol_class, args[0])

    if selector == "read" and sol_class.name == "String":
        import sys
        input_io = getattr(registry, "_input_io", None)
        line = sys.stdin.readline() if input_io is None else input_io.readline()

        if line.endswith("\n"):
            line = line[:-1]
        return SolString(registry.get_class("String"), line)

    raise InterpreterError(ErrorCode.SEM_UNDEF,
                           f"Class '{sol_class.name}' does not understand message '{selector}'")


def _invoke_user_method(receiver: SolObject, method_block: AstBlock, defining_cls: SolClass,
                        args: list[SolObject], registry: ClassRegistry) -> SolObject:
    """
    Invoke a user-defined method block on receiver.
    """

    #double check arity
    if len(args) != method_block.arity:
        raise InterpreterError(ErrorCode.INT_DNU,
                            f"Method expected {method_block.arity} arguments but got {len(args)}")

    #create dict for parameters
    params: dict[str, SolObject] = {
        param.name: arg_val
        for param, arg_val in zip(method_block.parameters, args, strict=True)
    }

    method_env = Enviroment(parent=None, params=params)

    #wrap ast block into SolBlock, self_obj is the receiver,
    # super_class is the class where the method is defined
    method_sol_block = SolBlock(sol_class=registry.get_class("Block"),
                ast_block=method_block, captured_env=method_env,
                self_obj=receiver, super_class=defining_cls)

    return execute_block(method_sol_block, [], registry)


def _handle_instance_attr(receiver: SolObject, selector: str, args: list[SolObject],
                        registry: ClassRegistry, super_class: SolClass | None) -> SolObject | None:
    """
    Handle instance attribute getter / setter.
    Returns the result if the selector matched an attribute operation,
    or None if no attribute handling applies
    """

    num_args = len(args)
    if num_args >= 2:
        return None

    #getter 0-arg selector
    if num_args == 0:
        if selector in receiver.instance_attrs:
            return receiver.instance_attrs[selector]
        #none -> DNU
        return None

    #setter 1-arg selector
    if not selector.endswith(":"):
        #always have to end with :
        return None

    #get rid of ':'
    attr_name = selector[:-1]

    #check if mehtod has same name as attribute - if yes, its a setter, depends on
    #recievers type (self, super or normal) where to look for the method
    search_start :SolClass | None = (super_class.parent
                                     if super_class is not None and super_class.parent is not None
                                     else receiver.sol_class)
    if _method_exist_in_chain(search_start, attr_name, registry):
        #its a setter, set the attribute
        raise InterpreterError(ErrorCode.INT_INST_ATTR,
                        f"Cannot set attribute '{attr_name}', a method with the same name exists")

    #check for builtins
    builtin_getter = find_builtin(receiver.sol_class.name, attr_name, registry)
    if builtin_getter is not None:
        raise InterpreterError(ErrorCode.INT_INST_ATTR,
                f"Cannot set attribute '{attr_name}', a built-in method with the same name exists")

    #create / update the attribute
    receiver.instance_attrs[attr_name] = args[0]
    return receiver


def _method_exist_in_chain(start_cls: SolClass | None, selector: str,
                           registry: ClassRegistry) -> bool:
    """
    Return True if any class in the chain starting at start_class
    defines a user method with the given 0-arg selector.
    """
    current_cls: SolClass | None = start_cls
    while current_cls is not None:
        if selector in current_cls.methods:
            return True
        current_cls = current_cls.parent
    return False




