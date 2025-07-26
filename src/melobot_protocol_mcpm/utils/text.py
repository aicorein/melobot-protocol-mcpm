from __future__ import annotations

import json
import re

from typing_extensions import Any, Literal, TypeAlias, cast

CommonColorType: TypeAlias = Literal[
    "black",
    "dark_blue",
    "dark_green",
    "dark_aqua",
    "dark_red",
    "dark_purple",
    "gold",
    "gray",
    "dark_gray",
    "blue",
    "green",
    "aqua",
    "red",
    "light_purple",
    "yellow",
    "white",
    "reset",
]

CommonColors = (
    "black",
    "dark_blue",
    "dark_green",
    "dark_aqua",
    "dark_red",
    "dark_purple",
    "gold",
    "gray",
    "dark_gray",
    "blue",
    "green",
    "aqua",
    "red",
    "light_purple",
    "yellow",
    "white",
    "reset",
)


class Color:
    black: Color
    dark_blue: Color
    dark_green: Color
    dark_aqua: Color
    dark_red: Color
    dark_purple: Color
    gold: Color
    gray: Color
    dark_gray: Color
    blue: Color
    green: Color
    aqua: Color
    red: Color
    light_purple: Color
    yellow: Color
    white: Color
    reset: Color

    def __init__(self, color: str) -> None:
        if color in CommonColors:
            self.value = color
            return
        if not color.startswith("#"):
            raise ValueError("Color value must start with '#'")
        try:
            if not (0x00000 <= int(color.lstrip("#"), 16) <= 0xFFFFFF):
                raise ValueError("Color value must be a valid hex color code")
        except ValueError:
            raise ValueError(f"Failed when parsing color: {color}") from None
        self.value = color

    @classmethod
    def from_hex(cls, color: str) -> Color:
        val = color.lstrip("#")
        if len(val) == 6 and re.match(r"^[0-9a-fA-F]+$", val):
            return cls(color)
        raise ValueError(f"Invalid hex color code: {color}")

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Color:
        color = (r, g, b)
        if not all(0 <= x <= 255 for x in color):
            raise ValueError(f"RGB values must be between 0 and 255, got {color}")
        value = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        return cls(value)


for cname in CommonColors:
    setattr(Color, cname, Color(cname))


class ClickEvent(dict):
    def __new__(
        cls,
        type: Literal[
            "open_url",
            "open_file",
            "run_command",
            "suggest_command",
            "change_page",
            "copy_to_clipboard",
        ],
        value: str,
    ) -> ClickEvent:
        return cast(ClickEvent, {"action": type, "value": value})


class HoverEvent:
    def __new__(
        cls, type: Literal["show_text", "show_item", "show_entity"], contents: dict
    ) -> HoverEvent:
        return cast(HoverEvent, {"action": type, "contents": contents})


class JsonText:
    def __init__(
        self,
        text: str | None = None,
        selector: str | None = None,
        color: Color | None = None,
        bold: bool = False,
        italic: bool = False,
        underlined: bool = False,
        strikethrough: bool = False,
        obfuscated: bool = False,
        insertion: str | None = None,
        click_event: ClickEvent | None = None,
        hover_event: HoverEvent | None = None,
    ) -> None:
        self._data: dict[str, Any]
        if text:
            self._data = {"text": text}
        if selector:
            self._data = {"selector": selector}
        if "text" in self._data.keys() and "selector" in self._data.keys():
            raise ValueError("text，selector 不能同时存在")
        if len(self._data.items()) == 0:
            raise ValueError("必须指定 text，selector 中的一个")

        if color:
            self._data["color"] = color.value
        if bold:
            self._data["bold"] = True
        if italic:
            self._data["italic"] = True
        if underlined:
            self._data["underlined"] = True
        if strikethrough:
            self._data["strikethrough"] = True
        if obfuscated:
            self._data["obfuscated"] = True
        if insertion:
            self._data["insertion"] = insertion
        if click_event:
            self._data["clickEvent"] = click_event
        if hover_event:
            self._data["hoverEvent"] = hover_event

    def format(self) -> str:
        return json.dumps(self._data, ensure_ascii=False)

    @staticmethod
    def formats(*content: str | JsonText) -> str:
        texts = [t if isinstance(t, JsonText) else JsonText(t) for t in content]
        return json.dumps([t._data for t in texts], ensure_ascii=False)
