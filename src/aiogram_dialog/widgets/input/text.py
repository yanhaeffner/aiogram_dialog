from __future__ import annotations

from abc import abstractmethod
from typing import (
    Any, Callable, Generic, Optional, Protocol, TypeVar, Union,
)

from aiogram.dispatcher.event.handler import FilterObject
from aiogram.types import ContentType, Message

from aiogram_dialog.api.protocols import DialogManager, DialogProtocol
from aiogram_dialog.widgets.common import ManagedWidget
from aiogram_dialog.widgets.widget_event import (
    ensure_event_processor,
    WidgetEventProcessor,
)
from .base import BaseInput

T = TypeVar("T")
TypeFactory = Callable[[str], T]


class OnSuccess(Protocol[T]):
    @abstractmethod
    async def __call__(
            self,
            message: Message,
            widget: TextInput,
            dialog_manager: DialogManager,
            data: T,
    ) -> Any:
        raise NotImplementedError


class OnError(Protocol[T]):
    @abstractmethod
    async def __call__(
            self,
            message: Message,
            widget: TextInput,
            dialog_manager: DialogManager,
    ) -> Any:
        raise NotImplementedError


class TextInput(BaseInput, Generic[T]):
    def __init__(
            self,
            id: str,
            type_factory: TypeFactory[T] = str,
            on_success: Union[OnSuccess[T], WidgetEventProcessor, None] = None,
            on_error: Union[OnError, WidgetEventProcessor, None] = None,
            filter: Optional[Callable[..., Any]] = None,
    ):
        super().__init__(id=id)
        if filter:
            self.filter = FilterObject(filter)
        else:
            self.filter = None
        self.type_factory = type_factory
        self.on_success = ensure_event_processor(on_success)
        self.on_error = ensure_event_processor(on_error)

    async def process_message(
            self,
            message: Message,
            dialog: DialogProtocol,
            manager: DialogManager,
    ) -> bool:
        if message.content_type != ContentType.TEXT:
            return False
        if self.filter and not await self.filter.call(
                manager.event, **manager.middleware_data,
        ):
            return False
        try:
            value = self.type_factory(message.text)
        except ValueError:
            await self.on_error.process_event(message, self, manager)
        else:
            # store original text
            self.set_widget_data(manager, message.text)
            await self.on_success.process_event(message, self, manager, value)
        return True

    def get_value(self, manager: DialogManager) -> T:
        return self.type_factory(self.get_widget_data(manager, None))

    def managed(self, manager: DialogManager):
        return ManagedTextInputAdapter(self, manager)


class ManagedTextInputAdapter(ManagedWidget[TextInput[T]], Generic[T]):
    def get_value(self) -> T:
        """Get last input data stored by widget."""
        return self.widget.get_value(self.manager)
