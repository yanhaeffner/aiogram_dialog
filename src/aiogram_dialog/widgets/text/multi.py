from typing import Any, Callable, Dict, Hashable, Optional, Union

from magic_filter import MagicFilter

from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.common import WhenCondition
from .base import Text

Selector = Callable[[Dict, "Case", DialogManager], Hashable]


def new_case_field(fieldname: str) -> Selector:
    def case_field(
            data: Dict, widget: "Case", manager: DialogManager,
    ) -> Hashable:
        return data.get(fieldname)

    return case_field


def new_magic_selector(f: MagicFilter) -> Selector:
    def when_magic(
            data: Dict, widget: "Case", manager: DialogManager,
    ) -> bool:
        return f.resolve(data)

    return when_magic


class Case(Text):
    def __init__(
            self,
            texts: Dict[Any, Text],
            selector: Union[str, Selector, MagicFilter],
            when: WhenCondition = None,
    ):
        super().__init__(when=when)
        self.texts = texts
        if isinstance(selector, str):
            self.selector = new_case_field(selector)
        elif isinstance(selector, MagicFilter):
            self.condition = new_magic_selector(selector)
        else:
            self.selector = selector
        self._has_default = ... in self.texts

    async def _render_text(self, data, manager: DialogManager) -> str:
        selection = self.selector(data, self, manager)
        if selection not in self.texts and self._has_default:
            selection = ...
        return await self.texts[selection].render_text(data, manager)

    def find(self, widget_id: str) -> Optional[Text]:
        for text in self.texts.values():
            if found := text.find(widget_id):
                return found
        return None
