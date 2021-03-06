import uuid
from typing import TYPE_CHECKING, Any, Optional

from ..jsonrpc2.protocol import ProtocolPartDescriptor
from ..language_server.protocol import LanguageServerProtocol
from ..language_server.types import (
    DocumentFilter,
    Model,
    TextDocumentChangeRegistrationOptions,
    TextDocumentRegistrationOptions,
    TextDocumentSyncKind,
)
from ..utils.logging import LoggingDescriptor
from .parts.completion import RobotCompletionProtocolPart
from .parts.diagnostics import RobotDiagnosticsProtocolPart
from .parts.documents_cache import DocumentsCache
from .parts.folding_range import RobotFoldingRangeProtocolPart
from .parts.goto import RobotGotoProtocolPart
from .parts.hover import RobotHoverProtocolPart
from .parts.signature_help import RobotSignatureHelpProtocolPart

if TYPE_CHECKING:
    from .server import RobotLanguageServer


def check_robotframework() -> None:
    try:
        __import__("robot")
    except ImportError as e:
        raise Exception("RobotFramework not found, please install.") from e


class Options(Model):
    storage_uri: Optional[str] = None
    global_storage_uri: Optional[str] = None


class RobotLanguageServerProtocol(LanguageServerProtocol):
    _logger = LoggingDescriptor()

    documents_cache = ProtocolPartDescriptor(DocumentsCache)
    _robot_diagnostics = ProtocolPartDescriptor(RobotDiagnosticsProtocolPart)
    _robot_folding_ranges = ProtocolPartDescriptor(RobotFoldingRangeProtocolPart)
    _robot_goto = ProtocolPartDescriptor(RobotGotoProtocolPart)
    _robot_hover = ProtocolPartDescriptor(RobotHoverProtocolPart)
    _robot_completion = ProtocolPartDescriptor(RobotCompletionProtocolPart)
    _signature_help = ProtocolPartDescriptor(RobotSignatureHelpProtocolPart)

    def __init__(self, server: "RobotLanguageServer"):
        super().__init__(server)
        self.options = Options()

    @_logger.call
    async def on_initialize(self, initialization_options: Optional[Any] = None) -> None:
        check_robotframework()

        if initialization_options is not None:
            self.options = Options.parse_obj(initialization_options)

        self._logger.info(f"initialized with {repr(self.options)}")

    @_logger.call
    async def on_initialized(self) -> None:
        document_selector = [DocumentFilter(language="python")]
        await self.register_capability(
            str(uuid.uuid4()),
            "textDocument/didOpen",
            TextDocumentRegistrationOptions(document_selector=document_selector),
        )
        await self.register_capability(
            str(uuid.uuid4()),
            "textDocument/didChange",
            TextDocumentChangeRegistrationOptions(
                document_selector=document_selector, sync_kind=TextDocumentSyncKind.INCREMENTAL
            ),
        )
        await self.register_capability(
            str(uuid.uuid4()),
            "textDocument/didClose",
            TextDocumentRegistrationOptions(document_selector=document_selector),
        )
