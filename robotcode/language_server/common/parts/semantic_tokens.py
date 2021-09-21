from __future__ import annotations

from asyncio import CancelledError
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Union

from ....jsonrpc2.protocol import rpc_method
from ....utils.async_event import async_tasking_event
from ....utils.logging import LoggingDescriptor
from ..has_extend_capabilities import HasExtendCapabilities
from ..language import HasLanguageId
from ..text_document import TextDocument
from ..types import (
    Range,
    SemanticTokenModifiers,
    SemanticTokens,
    SemanticTokensDelta,
    SemanticTokensDeltaParams,
    SemanticTokensDeltaPartialResult,
    SemanticTokensLegend,
    SemanticTokensOptions,
    SemanticTokensOptionsFull,
    SemanticTokensOptionsRange,
    SemanticTokensParams,
    SemanticTokensPartialResult,
    SemanticTokensRangeParams,
    SemanticTokenTypes,
    ServerCapabilities,
    TextDocumentIdentifier,
)

if TYPE_CHECKING:
    from ..protocol import LanguageServerProtocol

from .protocol_part import LanguageServerProtocolPart


class SemanticTokensProtocolPart(LanguageServerProtocolPart, HasExtendCapabilities):

    _logger = LoggingDescriptor()

    def __init__(self, parent: LanguageServerProtocol) -> None:
        super().__init__(parent)

    @async_tasking_event
    async def collect_full(
        sender, document: TextDocument, **kwargs: Any
    ) -> Union[SemanticTokens, SemanticTokensPartialResult, None]:
        ...

    @async_tasking_event
    async def collect_full_delta(
        sender, document: TextDocument, previous_result_id: str, **kwargs: Any
    ) -> Union[SemanticTokens, SemanticTokensDelta, SemanticTokensDeltaPartialResult, None]:
        ...

    @async_tasking_event
    async def collect_range(
        sender, document: TextDocument, range: Range, **kwargs: Any
    ) -> Union[SemanticTokens, SemanticTokensPartialResult, None]:
        ...

    token_types: List[Enum] = [e for e in SemanticTokenTypes]
    token_modifiers: List[Enum] = [e for e in SemanticTokenModifiers]

    def extend_capabilities(self, capabilities: ServerCapabilities) -> None:
        if len(self.collect_full) or len(self.collect_range):
            capabilities.semantic_tokens_provider = SemanticTokensOptions(
                legend=SemanticTokensLegend(
                    token_types=[e.value for e in self.token_types],
                    token_modifiers=[e.value for e in self.token_modifiers],
                ),
                full=SemanticTokensOptionsFull(delta=len(self.collect_full_delta) > 0)
                if len(self.collect_full)
                else None,
                range=SemanticTokensOptionsRange() if len(self.collect_range) else None,
            )

    @rpc_method(name="textDocument/semanticTokens/full", param_type=SemanticTokensParams)
    async def _text_document_semantic_tokens_full(
        self, text_document: TextDocumentIdentifier, *args: Any, **kwargs: Any
    ) -> Union[SemanticTokens, SemanticTokensPartialResult, None]:

        results: List[Union[SemanticTokens, SemanticTokensPartialResult]] = []
        document = self.parent.documents[text_document.uri]
        for result in await self.collect_full(
            self,
            document,
            callback_filter=lambda c: not isinstance(c, HasLanguageId) or c.__language_id__ == document.language_id,
            **kwargs,
        ):
            if isinstance(result, BaseException):
                if not isinstance(result, CancelledError):
                    self._logger.exception(result, exc_info=result)
            else:
                if result is not None:
                    results.append(result)

        # only the last is returned
        if len(results) > 0:
            return results[-1]

        return None

    @rpc_method(name="textDocument/semanticTokens/full/delta", param_type=SemanticTokensDeltaParams)
    async def _text_document_semantic_tokens_full_delta(
        self, text_document: TextDocumentIdentifier, previous_result_id: str, *args: Any, **kwargs: Any
    ) -> Union[SemanticTokens, SemanticTokensDelta, SemanticTokensDeltaPartialResult, None]:

        results: List[Union[SemanticTokens, SemanticTokensDelta, SemanticTokensDeltaPartialResult]] = []
        document = self.parent.documents[text_document.uri]
        for result in await self.collect_full_delta(
            self,
            document,
            previous_result_id,
            callback_filter=lambda c: not isinstance(c, HasLanguageId) or c.__language_id__ == document.language_id,
            **kwargs,
        ):
            if isinstance(result, BaseException):
                if not isinstance(result, CancelledError):
                    self._logger.exception(result, exc_info=result)
            else:
                if result is not None:
                    results.append(result)

        # only the last is returned
        if len(results) > 0:
            return results[-1]

        return None

    @rpc_method(name="textDocument/semanticTokens/range", param_type=SemanticTokensRangeParams)
    async def _text_document_semantic_tokens_range(
        self, text_document: TextDocumentIdentifier, range: Range, *args: Any, **kwargs: Any
    ) -> Union[SemanticTokens, SemanticTokensPartialResult, None]:

        results: List[Union[SemanticTokens, SemanticTokensPartialResult]] = []
        document = self.parent.documents[text_document.uri]
        for result in await self.collect_range(
            self,
            document,
            range,
            callback_filter=lambda c: not isinstance(c, HasLanguageId) or c.__language_id__ == document.language_id,
            **kwargs,
        ):
            if isinstance(result, BaseException):
                if not isinstance(result, CancelledError):
                    self._logger.exception(result, exc_info=result)
            else:
                if result is not None:
                    results.append(result)

        # only the last is returned
        if len(results) > 0:
            return results[-1]

        return None

    async def workspace_refresh(self) -> None:
        await self.parent.send_request("workspace/semanticTokens/refresh")
