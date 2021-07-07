from __future__ import annotations

import ast
from typing import (
    Any,
    AsyncIterator,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)

from ...common.types import Position, Range
from .async_ast import walk


def range_from_node(node: ast.AST) -> Range:
    return Range(
        start=Position(line=node.lineno - 1, character=node.col_offset),
        end=Position(
            line=node.end_lineno - 1 if node.end_lineno is not None else -1,
            character=node.end_col_offset if node.end_col_offset is not None else -1,
        ),
    )


@runtime_checkable
class Token(Protocol):
    type: Optional[str]
    value: str
    lineno: int
    col_offset: int
    error: Optional[str]

    @property
    def end_col_offset(self) -> int:
        ...

    def tokenize_variables(self) -> Iterator[Token]:
        ...


@runtime_checkable
class Statement(Protocol):
    tokens: Tuple[Token, ...]

    def get_token(self, type: str) -> Token:
        ...

    def get_tokens(self, *types: str) -> Tuple[Token, ...]:
        ...

    def get_value(self, type: str, default: Any = None) -> Any:
        ...

    def get_values(self, *types: str) -> Tuple[Any, ...]:
        ...

    @property
    def lineno(self) -> int:
        ...

    @property
    def col_offset(self) -> int:
        ...

    @property
    def end_lineno(self) -> int:
        ...

    @property
    def end_col_offset(self) -> int:
        ...


def range_from_token(token: Token) -> Range:
    return Range(
        start=Position(line=token.lineno - 1, character=token.col_offset),
        end=Position(
            line=token.lineno - 1,
            character=token.end_col_offset,
        ),
    )


def range_from_token_or_node(node: ast.AST, token: Optional[Token]) -> Range:
    if token is not None:
        return range_from_token(token)
    if node is not None:
        return range_from_node(node)
    return Range.zero()


def is_non_variable_token(token: Token) -> bool:
    from robot.errors import VariableError

    try:
        r = list(token.tokenize_variables())
        if len(r) == 1 and r[0] == token:
            return True
    except VariableError:
        pass
    return False


def whitespace_at_begin_of_token(token: Token) -> int:
    s = str(token.value)

    result = 0
    for c in s:
        if c == " ":
            result += 1
        elif c == "\t":
            result += 2
        else:
            break
    return result


def whitespace_from_begin_of_token(token: Token) -> str:
    s = str(token.value)

    result = ""
    for c in s:
        if c in [" ", "\t"]:
            result += c
        else:
            break

    return result


def get_tokens_at_position(node: Statement, position: Position) -> List[Token]:
    return [t for t in node.tokens if position.is_in_range(range := range_from_token(t)) or range.end == position]


def iter_nodes_at_position(node: ast.AST, position: Position) -> AsyncIterator[ast.AST]:
    return (n async for n in walk(node) if position.is_in_range(range := range_from_node(n)) or range.end == position)


async def get_nodes_at_position(node: ast.AST, position: Position) -> List[ast.AST]:
    return [n async for n in iter_nodes_at_position(node, position)]


async def get_node_at_position(node: ast.AST, position: Position) -> Optional[ast.AST]:
    result_nodes = await get_nodes_at_position(node, position)
    if not result_nodes:
        return None

    return result_nodes[-1]