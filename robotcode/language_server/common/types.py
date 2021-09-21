from __future__ import annotations

import re
from enum import Enum, IntEnum, IntFlag
from typing import Any, Dict, Iterator, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field

ProgressToken = Union[str, int]
DocumentUri = str
URI = str


class Model(BaseModel):
    class Config:
        allow_population_by_field_name = True
        # use_enum_values = True

        @classmethod
        def alias_generator(cls, string: str) -> str:
            string = re.sub(r"^[\-_\.]", "", str(string))
            if not string:
                return string
            return str(string[0]).lower() + re.sub(
                r"[\-_\.\s]([a-z])",
                lambda matched: str(matched.group(1)).upper(),
                string[1:],
            )


class CancelParams(Model):
    id: Union[int, str] = Field(...)


class WorkDoneProgressParams(Model):
    work_done_token: Optional[ProgressToken] = None


class ClientInfo(Model):
    name: str
    version: Optional[str] = None


class TraceValue(Enum):
    OFF = "off"
    MESSAGE = "message"
    VERBOSE = "verbose"


class WorkspaceFolder(Model):
    uri: DocumentUri
    name: str


class TextDocumentSyncClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    will_save: Optional[bool] = None
    will_save_wait_until: Optional[bool] = None
    did_save: Optional[bool] = None


class ResourceOperationKind(Enum):
    CREATE = "create"
    RENAME = "rename"
    DELETE = "delete"


class FailureHandlingKind(Enum):
    ABORT = "abort"
    TRANSACTIONAL = "transactional"
    TEXT_ONLY_TRANSACTIONAL = "textOnlyTransactional"
    UNDO = "undo"


class WorkspaceEditClientCapabilitiesChangeAnnotationSupport(Model):
    groups_on_label: Optional[bool] = None


class WorkspaceEditClientCapabilities(Model):
    document_changes: Optional[bool] = None
    resource_operations: Optional[List[ResourceOperationKind]] = None
    failure_handling: Optional[FailureHandlingKind] = None
    normalizes_line_endings: Optional[bool] = None

    change_annotation_support: Optional[WorkspaceEditClientCapabilitiesChangeAnnotationSupport] = None


class DidChangeConfigurationClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class DidChangeWatchedFilesClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class ExecuteCommandClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class SemanticTokensWorkspaceClientCapabilities(Model):
    refresh_support: Optional[bool] = None


class CodeLensWorkspaceClientCapabilities(Model):
    refresh_support: Optional[bool] = None


class SymbolKind(IntEnum):
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUMMEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPEPARAMETER = 26


class MarkupKind(Enum):
    PLAINTEXT = "plaintext"
    MARKDOWN = "markdown"


class CompletionItemTag(IntEnum):
    Deprecated = 1


class SymbolTag(IntEnum):
    Deprecated = 1


class InsertTextMode(IntEnum):
    AS_IS = 1
    ADJUST_INDENTATION = 2


class InsertTextFormat(Enum):
    PLAINTEXT = 1
    SNIPPET = 2


class WorkspaceSymbolClientCapabilitiesSymbolKind(Model):
    value_set: List[SymbolKind]


class WorkspaceSymbolClientCapabilitiesTagSupport(Model):
    value_set: List[SymbolTag]


class WorkspaceSymbolClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    symbol_kind: Optional[WorkspaceSymbolClientCapabilitiesSymbolKind] = None
    tag_support: Optional[WorkspaceSymbolClientCapabilitiesTagSupport] = None


class CompletionItemKind(IntEnum):
    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18
    FOLDER = 19
    ENUM_MEMBER = 20
    CONSTANT = 21
    STRUCT = 22
    EVENT = 23
    OPERATOR = 24
    TYPE_PARAMETER = 25


class CompletionClientCapabilitiesCompletionItemTagSupport(Model):
    value_set: List[CompletionItemTag]


class CompletionClientCapabilitiesCompletionItemResolveSupport(Model):
    properties: List[str]


class CompletionClientCapabilitiesCompletionItemInsertTextModeSupport(Model):
    value_set: List[InsertTextMode]


class CompletionClientCapabilitiesCompletionItem(Model):
    snippet_support: Optional[bool] = None
    commit_characters_support: Optional[bool] = None
    documentation_format: Optional[List[MarkupKind]] = None
    deprecated_support: Optional[bool] = None
    preselect_support: Optional[bool] = None
    tag_support: Optional[CompletionClientCapabilitiesCompletionItemTagSupport] = None
    insert_replace_support: Optional[bool] = None
    resolve_support: Optional[CompletionClientCapabilitiesCompletionItemResolveSupport]
    insert_text_mode_support: Optional[CompletionClientCapabilitiesCompletionItemInsertTextModeSupport]


class CompletionClientCapabilitiesCompletionItemKind(Model):
    value_set: Optional[List[CompletionItemKind]] = None


class CompletionClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    completion_item: Optional[CompletionClientCapabilitiesCompletionItem]
    completion_item_kind: Optional[CompletionClientCapabilitiesCompletionItemKind]
    context_support: Optional[bool] = None


class HoverClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    content_format: Optional[List[MarkupKind]] = None


class SignatureHelpClientCapabilitiesSignatureInformationParameterInformation(Model):
    label_offset_support: Optional[bool] = None


class SignatureHelpClientCapabilitiesSignatureInformation(Model):
    documentation_format: Optional[List[MarkupKind]] = None
    parameter_information: Optional[SignatureHelpClientCapabilitiesSignatureInformationParameterInformation] = None
    active_parameter_support: Optional[bool] = None


class SignatureHelpClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    signature_information: Optional[SignatureHelpClientCapabilitiesSignatureInformation] = None
    context_support: Optional[bool] = None


class DeclarationClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    link_support: Optional[bool] = None


class DefinitionClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    link_support: Optional[bool] = None


class TypeDefinitionClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    link_support: Optional[bool] = None


class ImplementationClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    link_support: Optional[bool] = None


class ReferenceClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class DocumentHighlightClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class DocumentSymbolClientCapabilitiesSymbolKind(Model):
    value_set: Optional[List[SymbolKind]] = None


class DocumentSymbolClientCapabilitiesTagSupport(Model):
    value_set: List[SymbolTag]


class DocumentSymbolClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    symbol_kind: Optional[DocumentSymbolClientCapabilitiesSymbolKind]
    hierarchical_document_symbol_support: Optional[bool] = None
    tag_support: Optional[DocumentSymbolClientCapabilitiesTagSupport] = None
    label_support: Optional[bool] = None


class CodeActionKind(str):
    EMPTY = ""
    QUICKFIX = "quickfix"
    REFACTOR = "refactor"
    REFACTOREXTRACT = "refactor.extract"
    REFACTORINLINE = "refactor.inline"
    REFACTORREWRITE = "refactor.rewrite"
    SOURCE = "source"
    SOURCEORGANIZEIMPORTS = "source.organizeImports"


class CodeActionClientCapabilitiesCodeActionLiteralSupportCodeActionKind(Model):
    value_set: Optional[List[CodeActionKind]] = None


class CodeActionClientCapabilitiesCodeActionLiteralSupport(Model):
    code_action_kind: CodeActionClientCapabilitiesCodeActionLiteralSupportCodeActionKind


class CodeActionClientCapabilitiesResolveSupport(Model):
    properties: List[str]


class CodeActionClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    code_action_literal_support: Optional[CodeActionClientCapabilitiesCodeActionLiteralSupport] = None
    is_preferred_support: Optional[bool] = None
    disabled_support: Optional[bool] = None
    data_support: Optional[bool] = None
    resolve_support: Optional[CodeActionClientCapabilitiesResolveSupport] = None
    honors_change_annotations: Optional[bool] = None


class CodeLensClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class DocumentLinkClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    tooltip_support: Optional[bool] = None


class DocumentColorClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class DocumentFormattingClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class DocumentRangeFormattingClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class DocumentOnTypeFormattingClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class PrepareSupportDefaultBehavior(IntEnum):
    Identifier = 1


class RenameClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    prepare_support: Optional[bool] = None
    prepare_support_default_behavior: Optional[PrepareSupportDefaultBehavior] = None
    honors_change_annotations: Optional[bool] = None


class DiagnosticTag(IntEnum):
    Unnecessary = 1
    Deprecated = 2


class PublishDiagnosticsClientCapabilitiesTagSupport(Model):
    value_set: List[DiagnosticTag]


class PublishDiagnosticsClientCapabilities(Model):
    related_information: Optional[bool] = None
    tag_support: Optional[PublishDiagnosticsClientCapabilitiesTagSupport] = None
    version_support: Optional[bool] = None
    code_description_support: Optional[bool] = None
    data_support: Optional[bool] = None


class FoldingRangeClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    range_limit: Optional[int] = None
    line_folding_only: Optional[bool] = None


class SelectionRangeClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class LinkedEditingRangeClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class CallHierarchyClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class TokenFormat(Enum):
    Relative = "relative"


class SemanticTokensClientCapabilitiesRequestsFull(Model):
    delta: Optional[bool] = None


class SemanticTokensClientCapabilitiesRequests(Model):
    range: Union[bool, Dict[Any, Any], None]
    full: Union[SemanticTokensClientCapabilitiesRequestsFull, bool, None] = None


class SemanticTokensClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    requests: SemanticTokensClientCapabilitiesRequests
    token_types: List[str]
    token_modifiers: List[str]
    formats: List[TokenFormat]
    overlapping_token_support: Optional[bool] = None
    multiline_token_support: Optional[bool] = None


class MonikerClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None


class TextDocumentClientCapabilities(Model):
    synchronization: Optional[TextDocumentSyncClientCapabilities] = None
    completion: Optional[CompletionClientCapabilities] = None
    hover: Optional[HoverClientCapabilities] = None
    signature_help: Optional[SignatureHelpClientCapabilities] = None
    declaration: Optional[DeclarationClientCapabilities] = None
    definition: Optional[DefinitionClientCapabilities] = None
    type_definition: Optional[TypeDefinitionClientCapabilities] = None
    implementation: Optional[ImplementationClientCapabilities] = None
    references: Optional[ReferenceClientCapabilities] = None
    document_highlight: Optional[DocumentHighlightClientCapabilities] = None
    document_symbol: Optional[DocumentSymbolClientCapabilities] = None
    code_action: Optional[CodeActionClientCapabilities] = None
    code_lens: Optional[CodeLensClientCapabilities] = None
    document_link: Optional[DocumentLinkClientCapabilities] = None
    color_provider: Optional[DocumentColorClientCapabilities] = None
    formatting: Optional[DocumentFormattingClientCapabilities] = None
    range_formatting: Optional[DocumentRangeFormattingClientCapabilities] = None
    on_type_formatting: Optional[DocumentOnTypeFormattingClientCapabilities] = None
    rename: Optional[RenameClientCapabilities] = None
    publish_diagnostics: Optional[PublishDiagnosticsClientCapabilities] = None
    folding_range: Optional[FoldingRangeClientCapabilities] = None
    selection_range: Optional[SelectionRangeClientCapabilities] = None
    linked_editing_range: Optional[LinkedEditingRangeClientCapabilities] = None
    call_hierarchy: Optional[CallHierarchyClientCapabilities] = None
    semantic_tokens: Optional[SemanticTokensClientCapabilities] = None
    moniker: Optional[MonikerClientCapabilities] = None


class ShowMessageRequestClientCapabilitiesMessageActionItem(Model):
    additional_properties_support: Optional[bool] = None


class ShowMessageRequestClientCapabilities(Model):
    message_action_item: Optional[ShowMessageRequestClientCapabilitiesMessageActionItem] = None


class ShowDocumentClientCapabilities(Model):
    support: bool


class RegularExpressionsClientCapabilities(Model):
    engine: str
    version: Optional[str] = None


class MarkdownClientCapabilities(Model):
    parser: str
    version: Optional[str] = None


class ClientCapabilitiesWorkspaceFileOperationsWorkspaceClientCapabilities(Model):
    dynamic_registration: Optional[bool] = None
    did_create: Optional[bool] = None
    will_create: Optional[bool] = None
    did_rename: Optional[bool] = None
    will_rename: Optional[bool] = None
    did_delete: Optional[bool] = None
    will_delete: Optional[bool] = None


class ClientCapabilitiesWorkspace(Model):
    apply_edit: Optional[bool] = None
    workspace_edit: Optional[WorkspaceEditClientCapabilities] = None
    did_change_configuration: Optional[DidChangeConfigurationClientCapabilities] = None
    did_change_watched_files: Optional[DidChangeWatchedFilesClientCapabilities] = None
    symbol: Optional[WorkspaceSymbolClientCapabilities] = None
    execute_command: Optional[ExecuteCommandClientCapabilities] = None
    workspace_folders: Optional[bool] = None
    configuration: Optional[bool] = None
    semantic_tokens: Optional[SemanticTokensWorkspaceClientCapabilities] = None
    code_lens: Optional[CodeLensWorkspaceClientCapabilities] = None
    file_operations: Optional[ClientCapabilitiesWorkspaceFileOperationsWorkspaceClientCapabilities]


class ClientCapabilitiesWindow(Model):
    work_done_progress: Optional[bool] = None
    show_message: Optional[ShowMessageRequestClientCapabilities] = None
    show_document: Optional[ShowDocumentClientCapabilities] = None


class ClientCapabilitiesGeneral(Model):
    regular_expressions: Optional[RegularExpressionsClientCapabilities] = None
    markdown: Optional[MarkdownClientCapabilities] = None


class ClientCapabilities(Model):
    workspace: Optional[ClientCapabilitiesWorkspace] = None
    text_document: Optional[TextDocumentClientCapabilities] = None
    window: Optional[ClientCapabilitiesWindow] = None
    general: Optional[ClientCapabilitiesGeneral] = None
    experimental: Optional[Any] = None


class InitializeParams(WorkDoneProgressParams):
    process_id: Optional[int] = None
    client_info: Optional[ClientInfo] = None
    locale: Optional[str] = None
    root_path: Optional[str] = None
    root_uri: Optional[DocumentUri] = None
    initialization_options: Optional[Any] = None
    capabilities: ClientCapabilities
    trace: Optional[TraceValue] = None
    workspace_folders: Optional[List[WorkspaceFolder]] = None


class InitializeError(Model):
    retry: bool


class WorkspaceFoldersServerCapabilities(Model):
    supported: Optional[bool] = None
    change_notifications: Union[str, bool, None] = None


class FileOperationPatternKind(Enum):
    FILE = "file"
    FOLDER = "folder"


class FileOperationPatternOptions(Model):
    ignore_case: Optional[bool] = None


class FileOperationPattern(Model):
    glob: str
    matches: Optional[FileOperationPatternKind]
    options: Optional[FileOperationPatternOptions]


class FileOperationFilter(Model):
    scheme: Optional[str] = None
    pattern: FileOperationPattern


class FileOperationRegistrationOptions(Model):
    filters: List[FileOperationFilter]


class TextDocumentSyncKind(Enum):
    NONE = 0
    FULL = 1
    INCREMENTAL = 2


class SaveOptions(Model):
    include_text: Optional[bool]


class TextDocumentSyncOptions(Model):
    open_close: Optional[bool] = None
    change: Optional[TextDocumentSyncKind] = None
    will_save: Optional[bool] = None
    will_save_wait_until: Optional[bool] = None
    save: Union[bool, SaveOptions, None] = None


class WorkDoneProgressOptions(Model):
    work_done_progress: Optional[bool] = None


class DocumentFilter(Model):
    language: Optional[str] = None
    scheme: Optional[str] = None
    pattern: Optional[str] = None


DocumentSelector = List[DocumentFilter]


class TextDocumentRegistrationOptions(Model):
    document_selector: Optional[DocumentSelector] = None


class StaticRegistrationOptions(Model):
    id: Optional[str] = None


class TextDocumentChangeRegistrationOptions(TextDocumentRegistrationOptions):
    sync_kind: TextDocumentSyncKind


class FoldingRangeOptions(WorkDoneProgressOptions):
    pass


class FoldingRangeRegistrationOptions(
    TextDocumentRegistrationOptions, FoldingRangeOptions, StaticRegistrationOptions, Model
):
    pass


class DefinitionOptions(WorkDoneProgressOptions):
    pass


class DeclarationOptions(WorkDoneProgressOptions):
    pass


class DeclarationRegistrationOptions(DeclarationOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions):
    pass


class ImplementationOptions(WorkDoneProgressOptions):
    pass


class ImplementationRegistrationOptions(DeclarationOptions, TextDocumentRegistrationOptions, StaticRegistrationOptions):
    pass


class HoverOptions(WorkDoneProgressOptions):
    pass


class WorkspaceSymbolOptions(WorkDoneProgressOptions):
    pass


class DocumentSymbolOptions(WorkDoneProgressOptions):
    label: Optional[str] = None


class DocumentSymbolRegistrationOptions(TextDocumentRegistrationOptions, DocumentSymbolOptions):
    pass


class ServerCapabilitiesWorkspaceFileOperations(Model):
    did_create: Optional[FileOperationRegistrationOptions] = None
    will_create: Optional[FileOperationRegistrationOptions] = None
    did_rename: Optional[FileOperationRegistrationOptions] = None
    will_rename: Optional[FileOperationRegistrationOptions] = None
    did_delete: Optional[FileOperationRegistrationOptions] = None
    will_delete: Optional[FileOperationRegistrationOptions] = None


class ServerCapabilitiesWorkspace(Model):
    workspace_folders: Optional[WorkspaceFoldersServerCapabilities] = None
    file_operations: Optional[ServerCapabilitiesWorkspaceFileOperations] = None


class CompletionOptions(WorkDoneProgressOptions):
    trigger_characters: Optional[List[str]] = None
    all_commit_characters: Optional[List[str]] = None
    resolve_provider: Optional[bool] = None


class CompletionRegistrationOptions(TextDocumentRegistrationOptions, CompletionOptions):
    pass


class SignatureHelpOptions(WorkDoneProgressOptions):
    trigger_characters: Optional[List[str]] = None
    retrigger_characters: Optional[List[str]] = None


class CodeLensOptions(WorkDoneProgressOptions):
    resolve_provider: Optional[bool]


class DocumentFormattingOptions(WorkDoneProgressOptions):
    pass


class DocumentFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentFormattingOptions):
    pass


class DocumentRangeFormattingOptions(WorkDoneProgressOptions):
    pass


class DocumentRangeFormattingRegistrationOptions(TextDocumentRegistrationOptions, DocumentRangeFormattingOptions):
    pass


class ExecuteCommandOptions(WorkDoneProgressOptions):
    commands: List[str]


class SemanticTokensLegend(Model):
    token_types: List[str]
    token_modifiers: List[str]


class SemanticTokensOptionsFull(Model):
    delta: Optional[bool] = None


class SemanticTokensOptionsRange(Model):
    pass


class SemanticTokensOptions(WorkDoneProgressOptions):
    legend: SemanticTokensLegend
    range: Union[bool, SemanticTokensOptionsRange, None] = None
    full: Union[bool, SemanticTokensOptionsFull, None] = None


class SemanticTokensRegistrationOptions(
    TextDocumentRegistrationOptions, SemanticTokensOptions, StaticRegistrationOptions
):
    pass


class ServerCapabilities(Model):
    text_document_sync: Union[TextDocumentSyncOptions, TextDocumentSyncKind, None]
    completion_provider: Optional[CompletionOptions] = None
    hover_provider: Union[bool, HoverOptions, None] = None
    signature_help_provider: Optional[SignatureHelpOptions] = None
    declaration_provider: Union[bool, DeclarationOptions, DeclarationRegistrationOptions, None] = None
    definition_provider: Union[bool, DefinitionOptions, None] = None
    implementation_provider: Union[bool, ImplementationOptions, ImplementationRegistrationOptions, None] = None
    # references_provider: Union[bool, ReferenceOptions, None] = None
    # document_highlight_provider: Union[bool, DocumentHighlightOptions, None] = None
    document_symbol_provider: Union[bool, DocumentSymbolOptions, None] = None
    # code_action_provider: Union[bool, CodeActionOptions] = None
    code_lens_provider: Optional[CodeLensOptions] = None
    # document_link_provider: Optional[DocumentLinkOptions] = None
    # color_provider: Union[bool, DocumentColorOptions, DocumentColorRegistrationOptions, None] = None
    document_formatting_provider: Union[bool, DocumentFormattingOptions, None] = None
    document_range_formatting_provider: Union[bool, DocumentRangeFormattingOptions, None] = None
    # document_on_type_formatting_provider: Optional[DocumentOnTypeFormattingOptions] = None
    # rename_provider: Union[bool, RenameOptions, None] = None
    folding_range_provider: Union[bool, FoldingRangeOptions, FoldingRangeRegistrationOptions, None] = None
    execute_command_provider: Optional[ExecuteCommandOptions] = None
    # selection_range_provider: Union[bool, SelectionRangeOptions, SelectionRangeRegistrationOptions, None] = None
    # linked_editing_range_provider: Union[
    #     boolean, LinkedEditingRangeOptions, LinkedEditingRangeRegistrationOptions, None
    # ] = None
    # call_hierarchy_provider: Union[boolean, CallHierarchyOptions, CallHierarchyRegistrationOptions, None] = None
    semantic_tokens_provider: Union[SemanticTokensOptions, SemanticTokensRegistrationOptions, None] = None
    # moniker_provider: Union[bool, MonikerOptions, MonikerRegistrationOptions, None] = None
    workspace_symbol_provider: Union[bool, WorkspaceSymbolOptions, None] = None
    workspace: Optional[ServerCapabilitiesWorkspace] = None
    experimental: Optional[Any] = None


class InitializeResultServerInfo(Model):
    name: str
    version: Optional[str] = None


class InitializeResult(Model):
    capabilities: ServerCapabilities
    server_info: Optional[InitializeResultServerInfo] = None


class InitializedParams(Model):
    pass


class DidChangeConfigurationParams(Model):
    settings: Any


class Position(Model):
    line: int
    character: int

    def __ge__(self, other: "Position") -> bool:
        line_gt = self.line > other.line

        if line_gt:
            return line_gt

        if self.line == other.line:
            return self.character >= other.character

        return False

    def __gt__(self, other: "Position") -> bool:
        line_gt = self.line > other.line

        if line_gt:
            return line_gt

        if self.line == other.line:
            return self.character > other.character

        return False

    def __le__(self, other: "Position") -> bool:
        line_lt = self.line < other.line

        if line_lt:
            return line_lt

        if self.line == other.line:
            return self.character <= other.character

        return False

    def __lt__(self, other: "Position") -> bool:
        line_lt = self.line < other.line

        if line_lt:
            return line_lt

        if self.line == other.line:
            return self.character < other.character

        return False

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __iter__(self) -> Iterator[int]:  # type: ignore
        return iter((self.line, self.character))

    def is_in_range(self, range: "Range") -> bool:
        return range.start <= self < range.end


class Range(Model):
    start: Position
    end: Position

    def __iter__(self) -> Iterator[Position]:  # type: ignore
        return iter((self.start, self.end))

    @staticmethod
    def zero() -> "Range":
        return Range(
            start=Position(
                line=0,
                character=0,
            ),
            end=Position(
                line=0,
                character=0,
            ),
        )

    def extend(self, start_line: int = 0, start_character: int = 0, end_line: int = 0, end_character: int = 0) -> Range:
        return Range(
            start=Position(line=self.start.line + start_line, character=self.start.character + start_character),
            end=Position(line=self.end.line + end_line, character=self.end.character + end_character),
        )


class TextDocumentItem(Model):
    uri: DocumentUri
    language_id: str
    version: int
    text: str


class DidOpenTextDocumentParams(Model):
    text_document: TextDocumentItem


class TextDocumentIdentifier(Model):
    uri: DocumentUri


class OptionalVersionedTextDocumentIdentifier(TextDocumentIdentifier):
    version: Optional[int] = None


class VersionedTextDocumentIdentifier(TextDocumentIdentifier):
    version: int


class DidCloseTextDocumentParams(Model):
    text_document: TextDocumentIdentifier


class TextDocumentContentRangeChangeEvent(Model):
    range: Range
    range_length: Optional[int] = None

    text: str


class TextDocumentContentTextChangeEvent(Model):
    text: str


TextDocumentContentChangeEvent = Union[TextDocumentContentRangeChangeEvent, TextDocumentContentTextChangeEvent]


class DidChangeTextDocumentParams(Model):
    text_document: VersionedTextDocumentIdentifier
    content_changes: List[TextDocumentContentChangeEvent]


class ConfigurationItem(Model):
    scope_uri: Optional[DocumentUri]
    section: Optional[str]


class ConfigurationParams(Model):
    items: List[ConfigurationItem]


class MessageType(IntEnum):
    Error = 1
    Warning = 2
    Info = 3
    Log = 4


class ShowMessageParams(Model):
    type: MessageType
    message: str


class LogMessageParams(Model):
    type: MessageType
    message: str


class MessageActionItem(Model):
    title: str


class ShowMessageRequestParams(ShowMessageParams):
    actions: Optional[List[MessageActionItem]] = None


class ShowDocumentParams(Model):
    uri: URI
    external: Optional[bool] = None
    take_focus: Optional[bool] = None
    selection: Optional[Range] = None


class ShowDocumentResult(Model):
    success: bool


class TextDocumentSaveReason(IntEnum):
    Manual = 1
    AfterDelay = 2
    FocusOut = 3


class WillSaveTextDocumentParams(Model):
    text_document: TextDocumentIdentifier
    reason: TextDocumentSaveReason


class TextEdit(Model):
    range: Range
    new_text: str


class DidSaveTextDocumentParams(Model):
    text_document: TextDocumentIdentifier
    text: Optional[str] = None


class DiagnosticSeverity(Enum):
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class CodeDescription(Model):
    href: URI


class Location(Model):
    uri: DocumentUri
    range: Range


class LocationLink(Model):
    origin_selection_range: Optional[Range]
    target_uri: DocumentUri
    target_range: Range
    target_selection_range: Range


class DiagnosticRelatedInformation(Model):
    location: Location
    message: str


class Diagnostic(Model):
    range: Range
    message: str
    severity: Optional[DiagnosticSeverity] = None
    code: Union[int, str, None] = None
    code_description: Optional[CodeDescription] = None
    source: Optional[str] = None
    tags: Optional[List[DiagnosticTag]] = None
    related_information: Optional[List[DiagnosticRelatedInformation]] = None
    data: Optional[Any] = None


class PublishDiagnosticsParams(Model):
    uri: DocumentUri
    version: Optional[int] = None
    diagnostics: List[Diagnostic]


class SetTraceParams(Model):
    value: TraceValue


class FoldingRangeParams(WorkDoneProgressParams):
    text_document: TextDocumentIdentifier


class FoldingRangeKind(Enum):
    Comment = "comment"
    Imports = "imports"
    Region = "region"


class FoldingRange(Model):
    start_line: int
    start_character: Optional[int] = None
    end_line: int
    end_character: Optional[int] = None
    kind: Union[FoldingRangeKind, str, None] = None


class FileCreate(Model):
    uri: str


class CreateFilesParams(Model):
    files: List[FileCreate]


class FileRename(Model):
    old_uri: str
    new_uri: str


class RenameFilesParams(Model):
    files: List[FileRename]


class FileDelete(Model):
    uri: str


class DeleteFilesParams(Model):
    files: List[FileDelete]


ChangeAnnotationIdentifier = str


class CreateFileOptions(Model):
    overwrite: Optional[bool] = None
    ignore_if_exists: Optional[bool] = None


class CreateFile(Model):
    kind: Literal["create"]
    uri: DocumentUri
    options: Optional[CreateFileOptions]
    annotation_id: ChangeAnnotationIdentifier


class RenameFileOptions(Model):
    overwrite: Optional[bool] = None
    ignore_if_exists: Optional[bool] = None


class RenameFile(Model):
    kind: Literal["rename"]
    old_uri: DocumentUri
    new_uri: DocumentUri
    options: Optional[RenameFileOptions]
    annotation_id: ChangeAnnotationIdentifier


class DeleteFileOptions(Model):
    recursive: Optional[bool] = None
    ignore_if_exists: Optional[bool] = None


class DeleteFile(Model):
    kind: Literal["delete"]
    uri: DocumentUri
    options: Optional[DeleteFileOptions]
    annotation_id: ChangeAnnotationIdentifier


class AnnotatedTextEdit(TextEdit):
    annotation_id: ChangeAnnotationIdentifier


class TextDocumentEdit(Model):
    text_document: OptionalVersionedTextDocumentIdentifier
    edits: Union[TextEdit, AnnotatedTextEdit]


class ChangeAnnotation(Model):
    label: str
    needs_confirmation: Optional[bool] = None
    description: Optional[str] = None


class WorkspaceEdit(Model):
    changes: Optional[Dict[DocumentUri, List[TextEdit]]] = None
    document_changes: Union[List[TextDocumentEdit], TextDocumentEdit, CreateFile, RenameFile, DeleteFile, None] = None
    change_annotations: Optional[Dict[ChangeAnnotationIdentifier, ChangeAnnotation]] = None


class PartialResultParams(Model):
    partial_result_token: Optional[ProgressToken]


class TextDocumentPositionParams(Model):
    text_document: TextDocumentIdentifier
    position: Position


class DefinitionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


class DeclarationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


class ImplementationParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    pass


class HoverParams(TextDocumentPositionParams, WorkDoneProgressParams):
    pass


class MarkedStringType(Model):
    language: str
    value: str


MarkedString = Union[str, MarkedStringType]


class MarkupContent(Model):
    kind: MarkupKind
    value: str


class Hover(Model):
    contents: Union[MarkedString, List[MarkedString], MarkupContent]
    range: Optional[Range] = None


class WorkspaceFoldersChangeEvent(Model):
    added: List[WorkspaceFolder]
    removed: List[WorkspaceFolder]


class DidChangeWorkspaceFoldersParams(Model):
    event: WorkspaceFoldersChangeEvent


class Registration(Model):
    id: str
    method: str
    register_options: Optional[Any]


class RegistrationParams(Model):
    registrations: List[Registration]


class Unregistration(Model):
    id: str
    method: str


class UnregistrationParams(Model):
    unregisterations: List[Unregistration]


class WatchKind(IntFlag):
    CREATE = 1
    CHANGE = 2
    DELETE = 4


class FileSystemWatcher(Model):
    glob_pattern: str
    kind: Optional[WatchKind]


class DidChangeWatchedFilesRegistrationOptions(Model):
    watchers: List[FileSystemWatcher]


class FileChangeType(IntEnum):
    CREATED = 1
    CHANGED = 2
    DELETED = 3


class FileEvent(Model):
    uri: DocumentUri
    type: FileChangeType


class DidChangeWatchedFilesParams(Model):
    changes: List[FileEvent]


class Command(Model):
    title: str
    command: str
    arguments: Optional[List[Any]] = None


class CompletionTriggerKind(Enum):
    INVOKED = 1
    TRIGGERCHARACTER = 2
    TRIGGERFORINCOMPLETECOMPLETIONS = 3


class CompletionContext(Model):
    trigger_kind: CompletionTriggerKind
    trigger_character: Optional[str]


class CompletionParams(TextDocumentPositionParams, WorkDoneProgressParams, PartialResultParams):
    context: Optional[CompletionContext]


class InsertReplaceEdit(Model):
    new_text: str
    insert: Range
    replace: Range


class CompletionItem(Model):
    label: str
    kind: Optional[CompletionItemKind] = None
    tags: Optional[List[CompletionItemTag]] = None
    detail: Optional[str] = None
    documentation: Union[str, MarkupContent, None] = None
    deprecated: Optional[bool] = None
    preselect: Optional[bool] = None
    sort_text: Optional[str] = None
    filter_text: Optional[str] = None
    insert_text: Optional[str] = None
    insert_text_format: Optional[InsertTextFormat] = None
    insert_text_mode: Optional[InsertTextMode] = None
    text_edit: Union[TextEdit, InsertReplaceEdit, None] = None
    additional_text_edits: Optional[List[TextEdit]]
    commit_characters: Optional[List[str]] = None
    command: Optional[Command] = None
    data: Optional[Any] = None


class CompletionList(Model):
    is_incomplete: bool
    items: List[CompletionItem]


class SignatureHelpTriggerKind(Enum):
    INVOKED = 1
    TRIGGERCHARACTER = 2
    CONTENTCHANGE = 3


class ParameterInformation(Model):
    label: Union[str, Tuple[int, int]]
    documentation: Union[str, MarkupContent, None] = None


class SignatureInformation(Model):
    label: str
    documentation: Union[str, MarkupContent, None] = None
    parameters: Optional[List[ParameterInformation]] = None
    active_parameter: Optional[int] = None


class SignatureHelp(Model):
    signatures: List[SignatureInformation]
    active_signature: Optional[int] = None
    active_parameter: Optional[int] = None


class SignatureHelpContext(Model):
    trigger_kind: SignatureHelpTriggerKind
    trigger_character: Optional[str] = None
    is_retrigger: bool
    active_signature_help: Optional[SignatureHelp] = None


class SignatureHelpParams(TextDocumentPositionParams, WorkDoneProgressParams):
    context: Optional[SignatureHelpContext] = None


class CodeLensParams(WorkDoneProgressParams, PartialResultParams):
    text_document: TextDocumentIdentifier


class CodeLens(Model):
    range: Range
    command: Optional[Command] = None
    data: Optional[Any] = None


class CodeLensRegistrationOptions(TextDocumentRegistrationOptions, CodeLensOptions):
    pass


class DocumentSymbolParams(WorkDoneProgressParams, PartialResultParams):
    text_document: TextDocumentIdentifier


class DocumentSymbol(Model):
    name: str
    detail: Optional[str] = None
    kind: SymbolKind
    tags: Optional[List[SymbolTag]] = None
    deprecated: Optional[bool] = None
    range: Range
    selection_range: Range
    children: Optional[List[DocumentSymbol]] = None


class SymbolInformation(Model):
    name: str
    kind: SymbolKind
    tags: Optional[List[SymbolTag]] = None
    deprecated: Optional[bool] = None
    location: Location
    container_name: Optional[str]


class FormattingOptions(Model):
    tab_size: int
    insert_spaces: bool
    trim_trailing_whitespace: Optional[bool] = None
    insert_final_newline: Optional[bool] = None
    trim_final_newlines: Optional[bool] = None


class DocumentFormattingParams(WorkDoneProgressParams):
    text_document: TextDocumentIdentifier
    options: FormattingOptions


class DocumentRangeFormattingParams(WorkDoneProgressParams):
    text_document: TextDocumentIdentifier
    range: Range
    options: FormattingOptions


class SemanticTokensParams(WorkDoneProgressParams, PartialResultParams):
    text_document: TextDocumentIdentifier


class SemanticTokens(Model):
    data: List[int]
    result_id: Optional[str] = None


class SemanticTokensPartialResult(Model):
    data: List[int]


class SemanticTokensDeltaParams(WorkDoneProgressParams, PartialResultParams):
    text_document: TextDocumentIdentifier
    previous_result_id: str


class SemanticTokensEdit(Model):
    start: int
    delete_count: int
    data: Optional[List[int]] = None


class SemanticTokensDelta(Model):
    edits: List[SemanticTokensEdit]
    result_id: Optional[str] = None


class SemanticTokensDeltaPartialResult(Model):
    edits: List[SemanticTokensEdit]


class SemanticTokensRangeParams(WorkDoneProgressParams, PartialResultParams):
    text_document: TextDocumentIdentifier
    range: Range


class SemanticTokenTypes(Enum):
    TYPE = "type"
    CLASS = "class"
    ENUM = "enum"
    INTERFACE = "interface"
    STRUCT = "struct"
    TYPE_PARAMETER = "typeParameter"
    PARAMETER = "parameter"
    VARIABLE = "variable"
    PROPERTY = "property"
    ENUM_MEMBER = "enumMember"
    EVENT = "event"
    FUNCTION = "function"
    METHOD = "method"
    MACRO = "macro"
    KEYWORD = "keyword"
    MODIFIER = "modifier"
    COMMENT = "comment"
    STRING = "string"
    NUMBER = "number"
    REGEXP = "regexp"
    OPERATOR = "operator"


class SemanticTokenModifiers(Enum):
    DECLARATION = "declaration"
    DEFINITION = "definition"
    READONLY = "readonly"
    STATIC = "static"
    DEPRECATED = "deprecated"
    ABSTRACT = "abstract"
    ASYNC = "async"
    MODIFICATION = "modification"
    DOCUMENTATION = "documentation"
    DEFAULT_LIBRARY = "defaultLibrary"
