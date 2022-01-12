from __future__ import annotations

import ast
import asyncio
import itertools
import weakref
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    cast,
)

from ....utils.async_itertools import async_chain
from ....utils.async_tools import CancelationToken, Lock, check_canceled
from ....utils.logging import LoggingDescriptor
from ....utils.uri import Uri
from ...common.lsp_types import (
    Diagnostic,
    DiagnosticRelatedInformation,
    DiagnosticSeverity,
    Location,
    Position,
    Range,
)
from ...common.text_document import TextDocument
from ..utils.ast import Token, range_from_node, tokenize_variables
from ..utils.async_ast import AsyncVisitor
from .entities import (
    ArgumentDefinition,
    BuiltInVariableDefinition,
    CommandLineVariableDefinition,
    Import,
    LibraryImport,
    ResourceImport,
    VariableDefinition,
    VariablesImport,
)
from .imports_manager import ImportsManager
from .library_doc import (
    BUILTIN_LIBRARY_NAME,
    BUILTIN_VARIABLES,
    DEFAULT_LIBRARIES,
    KeywordDoc,
    KeywordMatcher,
    LibraryDoc,
    VariableMatcher,
)

DIAGNOSTICS_SOURCE_NAME = "robotcode.namespace"


class DiagnosticsError(Exception):
    pass


class DiagnosticsWarningError(DiagnosticsError):
    pass


class ImportError(DiagnosticsError):
    pass


class NameSpaceError(Exception):
    pass


class VariablesVisitor(AsyncVisitor):
    async def get(self, source: str, model: ast.AST) -> List[VariableDefinition]:
        self._results: List[VariableDefinition] = []
        self.source = source
        await self.visit(model)
        return self._results

    async def visit_Section(self, node: ast.AST) -> None:  # noqa: N802
        from robot.parsing.model.blocks import VariableSection

        if isinstance(node, VariableSection):
            await self.generic_visit(node)

    async def visit_Variable(self, node: ast.AST) -> None:  # noqa: N802
        from robot.parsing.lexer.tokens import Token
        from robot.parsing.model.statements import Variable

        n = cast(Variable, node)
        name = n.get_token(Token.VARIABLE)
        if name is not None:
            self._results.append(
                VariableDefinition(
                    name=n.name,
                    name_token=name,
                    line_no=name.lineno,
                    col_offset=name.col_offset,
                    end_line_no=name.lineno,
                    end_col_offset=name.end_col_offset,
                    source=self.source,
                )
            )


class BlockVariableVisitor(AsyncVisitor):
    async def get(self, source: str, model: ast.AST, position: Optional[Position] = None) -> List[VariableDefinition]:
        self.source = source
        self.position = position

        self._results: Dict[str, VariableDefinition] = {}

        await self.visit(model)

        return list(self._results.values())

    async def visit(self, node: ast.AST) -> None:
        if self.position is None or self.position >= range_from_node(node).start:
            return await super().visit(node)

    async def visit_KeywordName(self, node: ast.AST) -> None:  # noqa: N802
        from robot.parsing.lexer.tokens import Token as RobotToken
        from robot.parsing.model.statements import KeywordName
        from robot.variables.search import VariableSearcher

        n = cast(KeywordName, node)
        name_token = cast(Token, n.get_token(RobotToken.KEYWORD_NAME))

        if name_token is not None and name_token.value:
            for variable_token in filter(
                lambda e: e.type == RobotToken.VARIABLE,
                tokenize_variables(name_token, identifiers="$", ignore_errors=True),
            ):
                if variable_token.value:
                    searcher = VariableSearcher("$", ignore_errors=True)
                    match = searcher.search(variable_token.value)
                    if match.base is None:
                        continue
                    name = f"{match.identifier}{{{match.base.split(':', 1)[0]}}}"

                    self._results[name] = ArgumentDefinition(
                        name=name,
                        name_token=variable_token,
                        line_no=variable_token.lineno,
                        col_offset=variable_token.col_offset,
                        end_line_no=variable_token.lineno,
                        end_col_offset=variable_token.end_col_offset,
                        source=self.source,
                    )

    def get_variable_token(self, token: Token) -> Optional[Token]:
        from robot.parsing.lexer.tokens import Token as RobotToken

        return next(
            (
                v
                for v in itertools.dropwhile(
                    lambda t: t.type in RobotToken.NON_DATA_TOKENS,
                    tokenize_variables(token, ignore_errors=True),
                )
                if v.type == RobotToken.VARIABLE
            ),
            None,
        )

    async def visit_Arguments(self, node: ast.AST) -> None:  # noqa: N802
        from robot.errors import VariableError
        from robot.parsing.lexer.tokens import Token as RobotToken
        from robot.parsing.model.statements import Arguments

        n = cast(Arguments, node)
        arguments = n.get_tokens(RobotToken.ARGUMENT)
        for argument_token in (cast(RobotToken, e) for e in arguments):
            try:
                argument = self.get_variable_token(argument_token)

                if argument is not None:
                    self._results[argument.value] = ArgumentDefinition(
                        name=argument.value,
                        name_token=argument,
                        line_no=argument.lineno,
                        col_offset=argument.col_offset,
                        end_line_no=argument.lineno,
                        end_col_offset=argument.end_col_offset,
                        source=self.source,
                    )

            except VariableError:
                pass

    async def visit_KeywordCall(self, node: ast.AST) -> None:  # noqa: N802
        from robot.errors import VariableError
        from robot.parsing.lexer.tokens import Token as RobotToken
        from robot.parsing.model.statements import KeywordCall

        # TODO  analyse "Set Local/Global/Suite Variable"

        n = cast(KeywordCall, node)
        for assign_token in n.get_tokens(RobotToken.ASSIGN):
            variable_token = self.get_variable_token(assign_token)
            try:
                if variable_token is not None and variable_token.value not in self._results:
                    self._results[variable_token.value] = VariableDefinition(
                        name=variable_token.value,
                        name_token=variable_token,
                        line_no=variable_token.lineno,
                        col_offset=variable_token.col_offset,
                        end_line_no=variable_token.lineno,
                        end_col_offset=variable_token.end_col_offset,
                        source=self.source,
                    )

            except VariableError:
                pass

    async def visit_ForHeader(self, node: ast.AST) -> None:  # noqa: N802
        from robot.parsing.lexer.tokens import Token as RobotToken
        from robot.parsing.model.statements import ForHeader

        n = cast(ForHeader, node)
        variables = n.get_tokens(RobotToken.VARIABLE)
        for variable in variables:
            variable_token = self.get_variable_token(variable)
            if variable_token is not None and variable_token.value and variable_token.value not in self._results:
                self._results[variable_token.value] = VariableDefinition(
                    name=variable_token.value,
                    name_token=variable_token,
                    line_no=node.lineno,
                    col_offset=node.col_offset,
                    end_line_no=variable_token.lineno,
                    end_col_offset=variable_token.end_col_offset,
                    source=self.source,
                )


class ImportVisitor(AsyncVisitor):
    async def get(self, source: str, model: ast.AST) -> List[Import]:
        self._results: List[Import] = []
        self.source = source
        await self.visit(model)
        return self._results

    async def visit_Section(self, node: ast.AST) -> None:  # noqa: N802
        from robot.parsing.model.blocks import SettingSection

        if isinstance(node, SettingSection):
            await self.generic_visit(node)

    async def visit_LibraryImport(self, node: ast.AST) -> None:  # noqa: N802
        from robot.parsing.lexer.tokens import Token as RobotToken
        from robot.parsing.model.statements import LibraryImport as RobotLibraryImport

        n = cast(RobotLibraryImport, node)
        name = cast(RobotToken, n.get_token(RobotToken.NAME))

        self._results.append(
            LibraryImport(
                name=n.name,
                name_token=name if name is not None else None,
                args=n.args,
                alias=n.alias,
                line_no=node.lineno,
                col_offset=node.col_offset,
                end_line_no=node.end_lineno if node.end_lineno is not None else -1,
                end_col_offset=node.end_col_offset if node.end_col_offset is not None else -1,
                source=self.source,
            )
        )

    async def visit_ResourceImport(self, node: ast.AST) -> None:  # noqa: N802
        from robot.parsing.lexer.tokens import Token as RobotToken
        from robot.parsing.model.statements import ResourceImport as RobotResourceImport

        n = cast(RobotResourceImport, node)
        name = cast(RobotToken, n.get_token(RobotToken.NAME))

        self._results.append(
            ResourceImport(
                name=n.name,
                name_token=name if name is not None else None,
                line_no=node.lineno,
                col_offset=node.col_offset,
                end_line_no=node.end_lineno if node.end_lineno is not None else -1,
                end_col_offset=node.end_col_offset if node.end_col_offset is not None else -1,
                source=self.source,
            )
        )

    async def visit_VariablesImport(self, node: ast.AST) -> None:  # noqa: N802
        from robot.parsing.lexer.tokens import Token as RobotToken
        from robot.parsing.model.statements import (
            VariablesImport as RobotVariablesImport,
        )

        n = cast(RobotVariablesImport, node)
        name = cast(RobotToken, n.get_token(RobotToken.NAME))

        self._results.append(
            VariablesImport(
                name=n.name,
                name_token=name if name is not None else None,
                args=n.args,
                line_no=node.lineno,
                col_offset=node.col_offset,
                end_line_no=node.end_lineno if node.end_lineno is not None else -1,
                end_col_offset=node.end_col_offset if node.end_col_offset is not None else -1,
                source=self.source,
            )
        )


@dataclass
class LibraryEntry:
    name: str
    import_name: str
    library_doc: LibraryDoc
    args: Tuple[Any, ...] = ()
    alias: Optional[str] = None
    import_range: Range = field(default_factory=lambda: Range.zero())
    import_source: str = ""

    def __str__(self) -> str:
        result = self.import_name
        if self.args:
            result += f"  {str(self.args)}"
        if self.alias:
            result += f"  WITH NAME  {self.alias}"
        return result


@dataclass
class ResourceEntry(LibraryEntry):
    imports: List[Import] = field(default_factory=lambda: [])
    variables: List[VariableDefinition] = field(default_factory=lambda: [])


@dataclass
class VariablesEntry(LibraryEntry):
    variables: List[VariableDefinition] = field(default_factory=lambda: [])


class Namespace:
    _logger = LoggingDescriptor()

    @_logger.call
    def __init__(
        self,
        imports_manager: ImportsManager,
        model: ast.AST,
        source: str,
        invalidated_callback: Callable[[Namespace], None],
        document: Optional[TextDocument] = None,
    ) -> None:
        super().__init__()

        self.imports_manager = imports_manager
        self.imports_manager.libraries_changed.add(self.libraries_changed)
        self.imports_manager.resources_changed.add(self.resources_changed)
        self.imports_manager.variables_changed.add(self.variables_changed)
        self.model = model
        self.source = source
        self.invalidated_callback = invalidated_callback
        self._document = weakref.ref(document) if document is not None else None
        self._libraries: OrderedDict[str, LibraryEntry] = OrderedDict()
        self._libraries_matchers: Optional[Dict[KeywordMatcher, LibraryEntry]] = None
        self._resources: OrderedDict[str, ResourceEntry] = OrderedDict()
        self._resources_matchers: Optional[Dict[KeywordMatcher, ResourceEntry]] = None
        self._variables: OrderedDict[str, VariablesEntry] = OrderedDict()
        self._initialized = False
        self._initialize_lock = Lock()
        self._analyzed = False
        self._analyze_lock = Lock()
        self._library_doc: Optional[LibraryDoc] = None
        self._library_doc_lock = Lock()
        self._imports: Optional[List[Import]] = None
        self._own_variables: Optional[List[VariableDefinition]] = None
        self._own_variables_lock = Lock()
        self._diagnostics: List[Diagnostic] = []
        self._keywords: Optional[List[KeywordDoc]] = None
        self._keywords_lock = Lock()

        # TODO: how to get the search order from model
        self.search_order: Tuple[str, ...] = ()

        self._finder: Optional[KeywordFinder] = None

    @property
    def document(self) -> Optional[TextDocument]:
        return self._document() if self._document is not None else None

    @_logger.call
    async def libraries_changed(self, sender: Any, libraries: List[LibraryDoc]) -> None:
        for p in libraries:
            if any(e for e in self._libraries.values() if e.library_doc == p):
                if self.document is not None:
                    self.document.set_data(Namespace.DataEntry, None)
                await self.invalidate()
                break

    @_logger.call
    async def resources_changed(self, sender: Any, resources: List[LibraryDoc]) -> None:
        for p in resources:
            if any(e for e in self._resources.values() if e.library_doc.source == p.source):
                if self.document is not None:
                    self.document.set_data(Namespace.DataEntry, None)
                await self.invalidate()
                break

    @_logger.call
    async def variables_changed(self, sender: Any, variables: List[LibraryDoc]) -> None:
        for p in variables:
            if any(e for e in self._variables.values() if e.library_doc.source == p.source):
                if self.document is not None:
                    self.document.set_data(Namespace.DataEntry, None)
                await self.invalidate()
                break

    async def invalidate(self) -> None:
        async with self._initialize_lock, self._library_doc_lock, self._analyze_lock:
            self._initialized = False

            self._libraries = OrderedDict()
            self._libraries_matchers = None
            self._resources = OrderedDict()
            self._resources_matchers = None
            self._variables = OrderedDict()
            self._imports = None
            self._own_variables = None
            self._keywords = None
            self._library_doc = None
            self._analyzed = False
            self._diagnostics = []
            self._finder = None

        self.invalidated_callback(self)

    @_logger.call
    async def get_diagnostisc(self, cancelation_token: Optional[CancelationToken] = None) -> List[Diagnostic]:
        await self.ensure_initialized()

        await self._analyze(cancelation_token)

        return self._diagnostics

    @_logger.call
    async def get_libraries(self) -> OrderedDict[str, LibraryEntry]:
        await self.ensure_initialized()

        return self._libraries

    async def get_libraries_matchers(self) -> Dict[KeywordMatcher, LibraryEntry]:
        if self._libraries_matchers is None:
            self._libraries_matchers = {
                KeywordMatcher(v.alias or v.name or v.import_name): v for v in (await self.get_libraries()).values()
            }
        return self._libraries_matchers

    async def get_resources(self) -> OrderedDict[str, ResourceEntry]:
        await self.ensure_initialized()

        return self._resources

    async def get_resources_matchers(self) -> Dict[KeywordMatcher, ResourceEntry]:
        if self._resources_matchers is None:
            self._resources_matchers = {
                KeywordMatcher(v.alias or v.name or v.import_name): v for v in (await self.get_resources()).values()
            }
        return self._resources_matchers

    @_logger.call
    async def get_library_doc(self) -> LibraryDoc:
        if self._library_doc is None:
            async with self._library_doc_lock:
                if self._library_doc is None:
                    self._library_doc = await self.imports_manager.get_libdoc_from_model(
                        self.model, self.source, model_type="RESOURCE"
                    )

        return self._library_doc

    class DataEntry(NamedTuple):
        libraries: OrderedDict[str, LibraryEntry] = OrderedDict()
        resources: OrderedDict[str, ResourceEntry] = OrderedDict()
        variables: OrderedDict[str, VariablesEntry] = OrderedDict()
        diagnostics: List[Diagnostic] = []

    @_logger.call
    async def ensure_initialized(self) -> bool:
        if not self._initialized:
            async with self._initialize_lock:
                if not self._initialized:

                    self._logger.debug(f"ensure_initialized -> initialize {self.document}")

                    imports = await self.get_imports()

                    data_entry: Optional[Namespace.DataEntry] = None
                    if self.document is not None:
                        # check or save several data in documents data cache,
                        # if imports are different, then the data is invalid
                        old_imports: List[Import] = self.document.get_data(Namespace)
                        if old_imports is None:
                            self.document.set_data(Namespace, imports)
                        elif old_imports != imports:
                            new_imports = []
                            for e in old_imports:
                                if e in imports:
                                    new_imports.append(e)
                            for e in imports:
                                if e not in new_imports:
                                    new_imports.append(e)
                            self.document.set_data(Namespace, new_imports)
                            self.document.set_data(Namespace.DataEntry, None)
                        else:
                            data_entry = self.document.get_data(Namespace.DataEntry)

                    if data_entry is not None:
                        self._libraries = data_entry.libraries.copy()
                        self._resources = data_entry.resources.copy()
                        self._variables = data_entry.variables.copy()
                        self._diagnostics = data_entry.diagnostics.copy()
                    else:
                        await self._import_default_libraries()
                        await self._import_imports(imports, str(Path(self.source).parent), top_level=True)

                        if self.document is not None:
                            self.document.set_data(
                                Namespace.DataEntry,
                                Namespace.DataEntry(
                                    self._libraries.copy(),
                                    self._resources.copy(),
                                    self._variables.copy(),
                                    self._diagnostics.copy(),
                                ),
                            )

                    self._initialized = True

        return self._initialized

    @property
    def initialized(self) -> bool:
        return self._initialized

    @_logger.call
    async def get_imports(self) -> List[Import]:
        if self._imports is None:
            self._imports = await ImportVisitor().get(self.source, self.model)

        return self._imports

    @_logger.call
    async def get_own_variables(self) -> List[VariableDefinition]:
        if self._own_variables is None:
            async with self._own_variables_lock:
                if self._own_variables is None:
                    self._own_variables = await VariablesVisitor().get(self.source, self.model)

        return self._own_variables

    _builtin_variables: Optional[List[BuiltInVariableDefinition]] = None

    @classmethod
    def get_builtin_variables(cls) -> List[BuiltInVariableDefinition]:
        if cls._builtin_variables is None:
            cls._builtin_variables = [BuiltInVariableDefinition(0, 0, 0, 0, "", n, None) for n in BUILTIN_VARIABLES]

        return cls._builtin_variables

    @_logger.call
    def get_command_line_variables(self) -> List[VariableDefinition]:
        if self.imports_manager.config is None:
            return []

        return [
            CommandLineVariableDefinition(0, 0, 0, 0, "", f"${{{k}}}", None)
            for k in self.imports_manager.config.variables.keys()
        ]

    @_logger.call
    async def get_variables(
        self, nodes: Optional[List[ast.AST]] = None, position: Optional[Position] = None
    ) -> Dict[VariableMatcher, VariableDefinition]:
        from robot.parsing.model.blocks import Keyword, TestCase

        await self.ensure_initialized()

        result: Dict[VariableMatcher, VariableDefinition] = {}

        async for var in async_chain(
            *[
                await BlockVariableVisitor().get(self.source, n, position)
                for n in nodes or []
                if isinstance(n, (Keyword, TestCase))
            ],
            (e for e in await self.get_own_variables()),
            *(e.variables for e in self._resources.values()),
            (e for e in self.get_command_line_variables()),
            *(e.variables for e in self._variables.values()),
            (e for e in self.get_builtin_variables()),
        ):
            if var.name is not None and VariableMatcher(var.name) not in result.keys():
                result[VariableMatcher(var.name)] = var

        return result

    @_logger.call
    async def find_variable(
        self, name: str, nodes: Optional[List[ast.AST]], position: Optional[Position] = None
    ) -> Optional[VariableDefinition]:
        return (await self.get_variables(nodes, position)).get(VariableMatcher(name), None)

    @_logger.call
    async def _import_imports(self, imports: Iterable[Import], base_dir: str, *, top_level: bool = False) -> None:
        async def _import(value: Import) -> Optional[LibraryEntry]:
            result: Optional[LibraryEntry] = None
            try:
                if isinstance(value, LibraryImport):
                    if value.name is None:
                        raise NameSpaceError("Library setting requires value.")

                    result = await self._get_library_entry(
                        value.name, value.args, value.alias, base_dir, sentinel=value
                    )
                    result.import_range = value.range()
                    result.import_source = value.source

                    if (
                        top_level
                        and result.library_doc.errors is None
                        and (len(result.library_doc.keywords) == 0 and not bool(result.library_doc.has_listener))
                    ):
                        self._diagnostics.append(
                            Diagnostic(
                                range=value.range(),
                                message=f"Imported library '{value.name}' contains no keywords.",
                                severity=DiagnosticSeverity.WARNING,
                                source=DIAGNOSTICS_SOURCE_NAME,
                            )
                        )
                elif isinstance(value, ResourceImport):
                    if value.name is None:
                        raise NameSpaceError("Resource setting requires value.")
                    source = await self.imports_manager.find_file(value.name, base_dir)

                    # allready imported
                    if any(r for r in self._resources.values() if r.library_doc.source == source):
                        return None

                    result = await self._get_resource_entry(value.name, base_dir, sentinel=value)
                    result.import_range = value.range()
                    result.import_source = value.source

                    if top_level and (
                        not result.library_doc.errors
                        and top_level
                        and not result.imports
                        and not result.variables
                        and not result.library_doc.keywords
                    ):
                        self._diagnostics.append(
                            Diagnostic(
                                range=value.range(),
                                message=f"Imported resource file '{value.name}' is empty.",
                                severity=DiagnosticSeverity.WARNING,
                                source=DIAGNOSTICS_SOURCE_NAME,
                            )
                        )

                elif isinstance(value, VariablesImport):
                    # TODO: variables

                    if value.name is None:
                        raise NameSpaceError("Variables setting requires value.")

                    result = await self._get_variables_entry(value.name, value.args, base_dir)

                    result.import_range = value.range()
                    result.import_source = value.source
                else:
                    raise DiagnosticsError("Unknown import type.")

                if top_level and result is not None:
                    if result.library_doc.source is not None and result.library_doc.errors:
                        if any(err.source for err in result.library_doc.errors):
                            self._diagnostics.append(
                                Diagnostic(
                                    range=value.range(),
                                    message="Import definition contains errors.",
                                    severity=DiagnosticSeverity.ERROR,
                                    source=DIAGNOSTICS_SOURCE_NAME,
                                    related_information=[
                                        DiagnosticRelatedInformation(
                                            location=Location(
                                                uri=str(Uri.from_path(err.source)),
                                                range=Range(
                                                    start=Position(
                                                        line=err.line_no - 1
                                                        if err.line_no is not None
                                                        else result.library_doc.line_no
                                                        if result.library_doc.line_no >= 0
                                                        else 0,
                                                        character=0,
                                                    ),
                                                    end=Position(
                                                        line=err.line_no - 1
                                                        if err.line_no is not None
                                                        else result.library_doc.line_no
                                                        if result.library_doc.line_no >= 0
                                                        else 0,
                                                        character=0,
                                                    ),
                                                ),
                                            ),
                                            message=err.message,
                                        )
                                        for err in result.library_doc.errors
                                        if err.source is not None
                                    ],
                                )
                            )
                        for err in filter(lambda e: e.source is None, result.library_doc.errors):
                            self._diagnostics.append(
                                Diagnostic(
                                    range=value.range(),
                                    message=err.message,
                                    severity=DiagnosticSeverity.ERROR,
                                    source=DIAGNOSTICS_SOURCE_NAME,
                                    code=err.type_name,
                                )
                            )
                    elif result.library_doc.errors is not None:
                        for err in result.library_doc.errors:
                            self._diagnostics.append(
                                Diagnostic(
                                    range=value.range(),
                                    message=err.message,
                                    severity=DiagnosticSeverity.ERROR,
                                    source=DIAGNOSTICS_SOURCE_NAME,
                                    code=err.type_name,
                                )
                            )

            except (asyncio.CancelledError, SystemExit, KeyboardInterrupt):
                raise
            except BaseException as e:
                if top_level:
                    self._diagnostics.append(
                        Diagnostic(
                            range=value.range(),
                            message=str(e),
                            severity=DiagnosticSeverity.ERROR,
                            source=DIAGNOSTICS_SOURCE_NAME,
                            code=type(e).__qualname__,
                        )
                    )
            return result

        for entry in await asyncio.gather(*(_import(v) for v in imports), return_exceptions=True):
            if isinstance(entry, (asyncio.CancelledError, SystemExit, KeyboardInterrupt)):
                raise entry

            if entry is not None:
                if isinstance(entry, ResourceEntry):
                    assert entry.library_doc.source is not None
                    allready_imported_resources = [
                        e for e in self._resources.values() if e.library_doc.source == entry.library_doc.source
                    ]

                    if not allready_imported_resources and entry.library_doc.source != self.source:
                        self._resources[entry.alias or entry.name or entry.import_name] = entry
                        try:
                            await self._import_imports(
                                entry.imports,
                                str(Path(entry.library_doc.source).parent),
                                top_level=False,
                            )
                        except (asyncio.CancelledError, SystemExit, KeyboardInterrupt):
                            raise
                        except BaseException as e:
                            if top_level:
                                self._diagnostics.append(
                                    Diagnostic(
                                        range=entry.import_range,
                                        message=str(e) or type(entry).__name__,
                                        severity=DiagnosticSeverity.ERROR,
                                        source=DIAGNOSTICS_SOURCE_NAME,
                                        code=type(e).__qualname__,
                                    )
                                )
                    else:
                        if top_level:
                            if entry.library_doc.source == self.source:
                                self._diagnostics.append(
                                    Diagnostic(
                                        range=entry.import_range,
                                        message="Recursive resource import.",
                                        severity=DiagnosticSeverity.INFORMATION,
                                        source=DIAGNOSTICS_SOURCE_NAME,
                                    )
                                )
                            elif allready_imported_resources and allready_imported_resources[0].library_doc.source:
                                self._resources[entry.alias or entry.name or entry.import_name] = entry

                                self._diagnostics.append(
                                    Diagnostic(
                                        range=entry.import_range,
                                        message="Resource already imported.",
                                        severity=DiagnosticSeverity.INFORMATION,
                                        source=DIAGNOSTICS_SOURCE_NAME,
                                        related_information=[
                                            DiagnosticRelatedInformation(
                                                location=Location(
                                                    uri=str(
                                                        Uri.from_path(allready_imported_resources[0].import_source)
                                                    ),
                                                    range=allready_imported_resources[0].import_range,
                                                ),
                                                message="",
                                            )
                                        ],
                                    )
                                )

                elif isinstance(entry, VariablesEntry):
                    allready_imported_variables = [
                        e
                        for e in self._variables.values()
                        if e.library_doc.source == entry.library_doc.source
                        and e.alias == entry.alias
                        and e.args == entry.args
                    ]
                    if top_level and allready_imported_variables and allready_imported_variables[0].library_doc.source:
                        self._diagnostics.append(
                            Diagnostic(
                                range=entry.import_range,
                                message=f'Variables "{entry}" already imported.',
                                severity=DiagnosticSeverity.INFORMATION,
                                source=DIAGNOSTICS_SOURCE_NAME,
                                related_information=[
                                    DiagnosticRelatedInformation(
                                        location=Location(
                                            uri=str(Uri.from_path(allready_imported_variables[0].import_source)),
                                            range=allready_imported_variables[0].import_range,
                                        ),
                                        message="",
                                    )
                                ],
                            )
                        )

                    if (entry.alias or entry.name or entry.import_name) not in self._variables:
                        self._variables[entry.alias or entry.name or entry.import_name] = entry

                elif isinstance(entry, LibraryEntry):
                    if top_level and entry.name == BUILTIN_LIBRARY_NAME and entry.alias is None:
                        self._diagnostics.append(
                            Diagnostic(
                                range=entry.import_range,
                                message=f'Library "{entry}" is not imported,'
                                ' because it would override the "BuiltIn" library.',
                                severity=DiagnosticSeverity.INFORMATION,
                                source=DIAGNOSTICS_SOURCE_NAME,
                                related_information=[
                                    DiagnosticRelatedInformation(
                                        location=Location(
                                            uri=str(Uri.from_path(entry.import_source)),
                                            range=entry.import_range,
                                        ),
                                        message="",
                                    )
                                ],
                            )
                        )
                        continue

                    allready_imported_library = [
                        e
                        for e in self._libraries.values()
                        if e.library_doc.source == entry.library_doc.source
                        and e.alias == entry.alias
                        and e.args == entry.args
                    ]
                    if top_level and allready_imported_library and allready_imported_library[0].library_doc.source:
                        self._diagnostics.append(
                            Diagnostic(
                                range=entry.import_range,
                                message=f'Library "{entry}" already imported.',
                                severity=DiagnosticSeverity.INFORMATION,
                                source=DIAGNOSTICS_SOURCE_NAME,
                                related_information=[
                                    DiagnosticRelatedInformation(
                                        location=Location(
                                            uri=str(Uri.from_path(allready_imported_library[0].import_source)),
                                            range=allready_imported_library[0].import_range,
                                        ),
                                        message="",
                                    )
                                ],
                            )
                        )

                    if (entry.alias or entry.name or entry.import_name) not in self._libraries:
                        self._libraries[entry.alias or entry.name or entry.import_name] = entry

    async def _import_default_libraries(self) -> None:
        async def _import_lib(library: str) -> Optional[LibraryEntry]:
            try:
                return await self._get_library_entry(
                    library, (), None, str(Path(self.source).parent), is_default_library=True
                )
            except (asyncio.CancelledError, SystemExit, KeyboardInterrupt):
                raise
            except BaseException as e:
                self._diagnostics.append(
                    Diagnostic(
                        range=Range.zero(),
                        message=f"Can't import default library '{library}': {str(e) or type(e).__name__}",
                        severity=DiagnosticSeverity.ERROR,
                        source="Robot",
                        code=type(e).__qualname__,
                    )
                )
                return None

        for e in await asyncio.gather(*(_import_lib(library) for library in DEFAULT_LIBRARIES)):
            if e is not None:
                self._libraries[e.alias or e.name or e.import_name] = e

    @_logger.call
    async def _get_library_entry(
        self,
        name: str,
        args: Tuple[Any, ...],
        alias: Optional[str],
        base_dir: str,
        *,
        is_default_library: bool = False,
        sentinel: Any = None,
    ) -> LibraryEntry:
        library_doc = await self.imports_manager.get_libdoc_for_library_import(
            name, args, base_dir=base_dir, sentinel=None if is_default_library else sentinel
        )

        return LibraryEntry(name=library_doc.name, import_name=name, library_doc=library_doc, args=args, alias=alias)

    @_logger.call
    async def _get_resource_entry(self, name: str, base_dir: str, sentinel: Any = None) -> ResourceEntry:
        namespace = await self.imports_manager.get_namespace_for_resource_import(name, base_dir, sentinel=sentinel)
        library_doc = await self.imports_manager.get_libdoc_for_resource_import(name, base_dir, sentinel=sentinel)

        return ResourceEntry(
            name=library_doc.name,
            import_name=name,
            library_doc=library_doc,
            imports=await namespace.get_imports(),
            variables=await namespace.get_own_variables(),
        )

    @_logger.call
    async def _get_variables_entry(
        self,
        name: str,
        args: Tuple[Any, ...],
        base_dir: str,
        sentinel: Any = None,
    ) -> VariablesEntry:
        library_doc = await self.imports_manager.get_libdoc_for_variables_import(
            name, args, base_dir=base_dir, sentinel=sentinel
        )

        return VariablesEntry(
            name=library_doc.name, import_name=name, library_doc=library_doc, args=args, variables=library_doc.variables
        )

    @_logger.call
    async def get_keywords(self) -> List[KeywordDoc]:
        if self._keywords is None:
            async with self._keywords_lock:
                if self._keywords is None:
                    await self.ensure_initialized()

                    result: Dict[KeywordMatcher, KeywordDoc] = {}

                    async for name, doc in async_chain(
                        (await self.get_library_doc()).keywords.items()
                        if (await self.get_library_doc()) is not None
                        else [],
                        *(e.library_doc.keywords.items() for e in self._resources.values()),
                        *(e.library_doc.keywords.items() for e in self._libraries.values()),
                    ):
                        if KeywordMatcher(name) not in result.keys():
                            result[KeywordMatcher(name)] = doc

                    self._keywords = list(result.values())

        return self._keywords

    @_logger.call
    async def _analyze(self, cancelation_token: Optional[CancelationToken] = None) -> None:
        from .analyzer import Analyzer

        if not self._analyzed:
            async with self._analyze_lock:
                if not self._analyzed:
                    canceled = False
                    try:
                        result = await Analyzer().get(self.model, self, cancelation_token)

                        await check_canceled()

                        self._diagnostics += result

                        lib_doc = await self.get_library_doc()

                        if lib_doc.errors is not None:
                            for err in lib_doc.errors:
                                self._diagnostics.append(
                                    Diagnostic(
                                        range=Range(
                                            start=Position(
                                                line=((err.line_no - 1) if err.line_no is not None else 0),
                                                character=0,
                                            ),
                                            end=Position(
                                                line=((err.line_no - 1) if err.line_no is not None else 0),
                                                character=0,
                                            ),
                                        ),
                                        message=err.message,
                                        severity=DiagnosticSeverity.ERROR,
                                        source=DIAGNOSTICS_SOURCE_NAME,
                                        code=err.type_name,
                                    )
                                )
                    except asyncio.CancelledError:
                        canceled = True
                        self._logger.debug("analyzing canceled")
                        raise
                    finally:
                        self._analyzed = not canceled
                        self._logger.debug(
                            lambda: f"analyzed {self.document}" if self._analyzed else f"not analyzed {self.document}"
                        )

    async def get_finder(self) -> KeywordFinder:
        if self._finder is None:
            await self.ensure_initialized()
            self._finder = KeywordFinder(self)
        return self._finder

    @_logger.call(condition=lambda self, name: self._finder is not None and name not in self._finder._cache)
    async def find_keyword(self, name: Optional[str]) -> Optional[KeywordDoc]:
        if self._finder is not None:
            return await self._finder.find_keyword(name)

        return await (await self.get_finder()).find_keyword(name)


class DiagnosticsEntry(NamedTuple):
    message: str
    severity: DiagnosticSeverity
    code: Optional[str] = None


class CancelSearchError(Exception):
    pass


class KeywordFinder:
    def __init__(self, namespace: Namespace) -> None:
        super().__init__()
        self.namespace = namespace
        self.diagnostics: List[DiagnosticsEntry] = []
        self.self_library_doc: Optional[LibraryDoc] = None
        self._cache: Dict[Optional[str], Tuple[Optional[KeywordDoc], List[DiagnosticsEntry]]] = {}

    def reset_diagnostics(self) -> None:
        self.diagnostics = []

    async def find_keyword(self, name: Optional[str]) -> Optional[KeywordDoc]:
        try:
            self.reset_diagnostics()

            cached = self._cache.get(name, None)

            if cached is not None:
                self.diagnostics = cached[1]
                return cached[0]
            else:
                result = await self._find_keyword(name)
                if result is None:
                    self.diagnostics.append(
                        DiagnosticsEntry(
                            f"No keyword with name {repr(name)} found.", DiagnosticSeverity.ERROR, "KeywordError"
                        )
                    )
                self._cache[name] = (result, self.diagnostics)

                return result
        except CancelSearchError:
            return None

    async def _find_keyword(self, name: Optional[str]) -> Optional[KeywordDoc]:
        if not name:
            self.diagnostics.append(
                DiagnosticsEntry("Keyword name cannot be empty.", DiagnosticSeverity.ERROR, "KeywordError")
            )
            raise CancelSearchError()
        if not isinstance(name, str):
            self.diagnostics.append(
                DiagnosticsEntry("Keyword name must be a string.", DiagnosticSeverity.ERROR, "KeywordError")
            )
            raise CancelSearchError()

        result = await self._get_keyword_from_self(name)
        if not result and "." in name:
            result = await self._get_explicit_keyword(name)

        if not result:
            result = await self._get_implicit_keyword(name)

        if not result:
            result = await self._get_bdd_style_keyword(name)

        return result

    async def _get_keyword_from_self(self, name: str) -> Optional[KeywordDoc]:
        if self.self_library_doc is None:
            self.self_library_doc = await self.namespace.get_library_doc()
        return self.self_library_doc.keywords.get(name, None)

    async def _yield_owner_and_kw_names(self, full_name: str) -> AsyncGenerator[Tuple[str, ...], None]:
        tokens = full_name.split(".")
        for i in range(1, len(tokens)):
            yield ".".join(tokens[:i]), ".".join(tokens[i:])

    async def _get_explicit_keyword(self, name: str) -> Optional[KeywordDoc]:
        found: List[Tuple[LibraryEntry, KeywordDoc]] = []
        async for owner_name, kw_name in self._yield_owner_and_kw_names(name):
            found.extend(await self.find_keywords(owner_name, kw_name))
        if len(found) > 1:
            self.diagnostics.append(
                DiagnosticsEntry(
                    self._create_multiple_keywords_found_message(name, found, implicit=False),
                    DiagnosticSeverity.ERROR,
                    "KeywordError",
                )
            )
            raise CancelSearchError()

        return found[0][1] if found else None

    async def find_keywords(self, owner_name: str, name: str) -> Sequence[Tuple[LibraryEntry, KeywordDoc]]:
        from robot.utils.match import eq

        return [
            (v, v.library_doc.keywords[name])
            async for v in async_chain(self.namespace._libraries.values(), self.namespace._resources.values())
            if eq(v.alias or v.name, owner_name) and name in v.library_doc.keywords
        ]

    def _create_multiple_keywords_found_message(
        self, name: str, found: Sequence[Tuple[LibraryEntry, KeywordDoc]], implicit: bool = True
    ) -> str:

        error = "Multiple keywords with name '%s' found" % name
        if implicit:
            error += ". Give the full name of the keyword you want to use"
        names = sorted(f"{e[0].alias or e[0].name}.{e[1].name}" for e in found)
        return "\n    ".join([error + ":"] + names)

    async def _get_implicit_keyword(self, name: str) -> Optional[KeywordDoc]:
        result = await self._get_keyword_from_resource_files(name)
        if not result:
            result = await self._get_keyword_from_libraries(name)
        return result

    async def _get_keyword_from_resource_files(self, name: str) -> Optional[KeywordDoc]:
        found: List[Tuple[LibraryEntry, KeywordDoc]] = [
            (v, v.library_doc.keywords[name])
            async for v in async_chain(self.namespace._resources.values())
            if name in v.library_doc.keywords
        ]
        if not found:
            return None
        if len(found) > 1:
            found = await self._get_keyword_based_on_search_order(found)
        if len(found) == 1:
            return found[0][1]

        self.diagnostics.append(
            DiagnosticsEntry(
                self._create_multiple_keywords_found_message(name, found),
                DiagnosticSeverity.ERROR,
                "KeywordError",
            )
        )
        raise CancelSearchError()

    async def _get_keyword_based_on_search_order(
        self, entries: List[Tuple[LibraryEntry, KeywordDoc]]
    ) -> List[Tuple[LibraryEntry, KeywordDoc]]:
        from robot.utils.match import eq

        for libname in self.namespace.search_order:
            for e in entries:
                if eq(libname, e[0].alias or e[0].name):
                    return [e]

        return entries

    async def _get_keyword_from_libraries(self, name: str) -> Optional[KeywordDoc]:
        found = [
            (v, v.library_doc.keywords[name])
            async for v in async_chain(self.namespace._libraries.values())
            if name in v.library_doc.keywords
        ]
        if not found:
            return None
        if len(found) > 1:
            found = await self._get_keyword_based_on_search_order(found)
        if len(found) == 2:
            found = await self._filter_stdlib_runner(*found)
        if len(found) == 1:
            return found[0][1]

        self.diagnostics.append(
            DiagnosticsEntry(
                self._create_multiple_keywords_found_message(name, found),
                DiagnosticSeverity.ERROR,
                "KeywordError",
            )
        )
        raise CancelSearchError()

    async def _filter_stdlib_runner(
        self, entry1: Tuple[LibraryEntry, KeywordDoc], entry2: Tuple[LibraryEntry, KeywordDoc]
    ) -> List[Tuple[LibraryEntry, KeywordDoc]]:
        from robot.libraries import STDLIBS

        stdlibs_without_remote = STDLIBS - {"Remote"}
        if entry1[0].name in stdlibs_without_remote:
            standard, custom = entry1, entry2
        elif entry2[0].name in stdlibs_without_remote:
            standard, custom = entry2, entry1
        else:
            return [entry1, entry2]

        self.diagnostics.append(
            DiagnosticsEntry(
                self._create_custom_and_standard_keyword_conflict_warning_message(custom, standard),
                DiagnosticSeverity.WARNING,
                "KeywordError",
            )
        )

        return [custom]

    def _create_custom_and_standard_keyword_conflict_warning_message(
        self, custom: Tuple[LibraryEntry, KeywordDoc], standard: Tuple[LibraryEntry, KeywordDoc]
    ) -> str:
        custom_with_name = standard_with_name = ""
        if custom[0].alias is not None:
            custom_with_name = " imported as '%s'" % custom[0].alias
        if standard[0].alias is not None:
            standard_with_name = " imported as '%s'" % standard[0].alias
        return (
            f"Keyword '{standard[1].name}' found both from a custom test library "
            f"'{custom[0].name}'{custom_with_name} and a standard library '{standard[1].name}'{standard_with_name}. "
            f"The custom keyword is used. To select explicitly, and to get "
            f"rid of this warning, use either '{custom[0].alias or custom[0].name}.{custom[1].name}' "
            f"or '{standard[0].alias or standard[0].name}.{standard[1].name}'."
        )

    async def _get_bdd_style_keyword(self, name: str) -> Optional[KeywordDoc]:
        lower = name.lower()
        for prefix in ["given ", "when ", "then ", "and ", "but "]:
            if lower.startswith(prefix):
                return await self._find_keyword(name[len(prefix) :])  # noqa: E203

        return None
