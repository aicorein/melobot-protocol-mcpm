from __future__ import annotations

import re

from melobot.adapter import Event as RootEvent
from melobot.adapter import TextEvent as RootTextEvent
from melobot.adapter import content
from typing_extensions import Generic, Literal, cast

from ..const import PROTOCOL_IDENTIFIER
from ..io.manager import ServerManager
from ..io.model import InputDataT, InputType, LogInputData
from ..utils.common import truncate
from ..utils.pattern import RegexPatternGroup as PatternGroup
from ..utils.pattern import fullmatch, search


class Event(RootEvent, Generic[InputDataT]):
    def __init__(self, server_id: str, data: InputDataT) -> None:
        super().__init__(PROTOCOL_IDENTIFIER)
        self.server_id = server_id
        self.scope: tuple[str, ...] = (self.server_id,)
        self.type = data.type
        self.raw = data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.type}, server={self.server_id!r})"

    @classmethod
    def resolve(cls, server_id: str, data: InputDataT) -> Event:
        cls_map: dict[InputType, type[Event]] = {InputType.LOG: LogEvent}
        if (etype := data.type) in cls_map:
            return cls_map[etype].resolve(server_id, data)
        return cls(server_id, data)

    def is_from_server(self, server_id: str) -> bool:
        return self.server_id == server_id

    def is_log(self) -> bool:
        return self.type == InputType.LOG


class LogEvent(RootTextEvent, Event[LogInputData]):
    def __init__(self, server_id: str, data: LogInputData) -> None:
        super().__init__(server_id, data)
        self.pattern_group = data.pattern_group
        self.cmd_factory = data.cmd_factory

        self.text = data.content.strip("\n")
        self.textlines = self.text.split("\n")

        matched = search(data.pattern_group.line, self.text)
        self.log_matched: re.Match | None
        if matched is not None:
            self.log_hms = tuple(
                map(
                    int,
                    (matched.group("hour"), matched.group("min"), matched.group("sec")),
                )
            )
            self.hour, self.min, self.sec = self.log_hms
            self.log_level: str = matched.group("logging").strip()
            self.log_content: str = matched.group("content").strip()
            self.log_matched = matched
            self.contents = (content.TextContent(self.log_content),)
        else:
            self.log_hms = (-1, -1, -1)
            self.hour, self.min, self.sec = self.log_hms
            self.log_level = ""
            self.log_content = self.text.strip()
            self.log_matched = None
            self.contents = (content.TextContent(self.text),)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(raw={truncate(self.log_content, 100)!r}, server={self.server_id!r})"

    @classmethod
    def resolve(cls, server_id: str, data: LogInputData) -> LogEvent:
        line_matched = search(data.pattern_group.line, data.content)
        if line_matched is None:
            return cls(server_id, data)

        log_content: str = line_matched.group("content").strip()
        is_msg, pattern = MessageEvent._is_message(data.pattern_group, log_content)
        if is_msg:
            return MessageEvent(server_id, cast(re.Pattern, pattern), data)

        is_player_operation, pattern, operation_type = PlayerEvent._is_player_operation(
            data.pattern_group, log_content
        )
        if is_player_operation:
            return PlayerEvent(
                server_id,
                cast(re.Pattern, pattern),
                cast(Literal["joined", "left"], operation_type),
                data,
            )

        is_server_done, pattern = ServerDoneEvent._is_server_done(
            data.pattern_group, log_content
        )
        if is_server_done:
            return ServerDoneEvent(server_id, cast(re.Pattern, pattern), data)

        is_rcon_started, pattern = RconStartedEvent._is_rcon_started(
            data.pattern_group, log_content
        )
        if is_rcon_started:
            return RconStartedEvent(server_id, cast(re.Pattern, pattern), data)

        return cls(server_id, data)

    def is_message(self) -> bool:
        return isinstance(self, MessageEvent)

    def is_player_event(self) -> bool:
        return isinstance(self, PlayerEvent)

    def is_server_done(self) -> bool:
        return isinstance(self, ServerDoneEvent)

    def is_rcon_started(self) -> bool:
        return isinstance(self, RconStartedEvent)


class MessageEvent(LogEvent):
    def __init__(self, server_id: str, pattern: re.Pattern, data: LogInputData) -> None:
        super().__init__(server_id, data)
        self.pattern = pattern
        matched = fullmatch(self.pattern, self.log_content)
        if matched is None:
            raise ValueError(
                f"无法解析的消息行: {self.log_content}，你可能需要检查正则表达式"
            )

        self.player_name: str = matched.group("name")
        if fullmatch(data.pattern_group.player_name, self.player_name) is None:
            raise ValueError(
                f"无效的玩家名称: {self.player_name}，原始文本：{self.log_content!r}"
            )

        self.message: str = matched.group("message")
        self.text = self.message
        self.textlines = self.text.split("\n")
        self.msg_matched = matched
        self.contents = (content.TextContent(self.message),)
        self.scope = (self.server_id, self.player_name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(player={self.player_name!r}, msg={truncate(self.message, 100)!r}, server={self.server_id!r})"

    def is_from_player(self, player_name: str) -> bool:
        return self.player_name == player_name

    @classmethod
    def _is_message(
        cls, pattern_grp: PatternGroup, text: str
    ) -> tuple[bool, re.Pattern | None]:
        for pattern in pattern_grp.msg:
            if (matched := fullmatch(pattern, text)) is not None:
                player_name = matched.group("name")
                if fullmatch(pattern_grp.player_name, player_name) is not None:
                    return True, pattern
        return False, None


class PlayerEvent(LogEvent):
    def __init__(
        self,
        server_id: str,
        pattern: re.Pattern,
        type: Literal["joined", "left"],
        data: LogInputData,
    ) -> None:
        super().__init__(server_id, data)
        self.operation_type = type
        self.pattern = pattern
        matched = fullmatch(self.pattern, self.log_content)
        if matched is None:
            raise ValueError(f"无法解析的玩家事件: {self.log_content}")

        self.player_name: str = matched.group("name")

        if fullmatch(data.pattern_group.player_name, self.player_name) is None:
            raise ValueError(
                f"无效的玩家名称: {self.player_name}，原始文本：{self.log_content!r}"
            )
        self.operation_matched = matched

        self.contents = (
            content.TextContent(
                f"{self.player_name} {self.operation_type} the server named {self.server_id}"
            ),
        )
        self.scope = (self.server_id, self.player_name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(player={self.player_name!r}, operation={self.operation_type!r}, server={self.server_id!r})"

    def is_from_player(self, player_name: str) -> bool:
        return self.player_name == player_name

    def is_joined(self) -> bool:
        return self.operation_type == "joined"

    def is_left(self) -> bool:
        return self.operation_type == "left"

    @classmethod
    def _is_player_operation(
        cls, pattern_grp: PatternGroup, text: str
    ) -> tuple[bool, re.Pattern | None, Literal["joined", "left"] | None]:
        mapping: dict[re.Pattern, Literal["joined", "left"]] = {
            pattern_grp.player_joined: "joined",
            pattern_grp.player_left: "left",
        }
        patterns = (pattern_grp.player_joined, pattern_grp.player_left)
        for pattern in patterns:
            if (matched := fullmatch(pattern, text)) is not None:
                player_name = matched.group("name")
                if fullmatch(pattern_grp.player_name, player_name) is not None:
                    return True, pattern, mapping[pattern]
        return False, None, None


class ServerDoneEvent(LogEvent):
    def __init__(self, server_id: str, pattern: re.Pattern, data: LogInputData) -> None:
        super().__init__(server_id, data)
        self.pattern = pattern
        matched = fullmatch(self.pattern, self.log_content)
        if matched is None:
            raise ValueError(f"无法解析的服务器启动完成事件: {self.log_content}")

        self.server_done_matched = matched
        self.contents = (content.TextContent(f"Server {self.server_id} has loaded."),)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(server={self.server_id!r})"

    @classmethod
    def _is_server_done(
        cls, pattern_grp: PatternGroup, text: str
    ) -> tuple[bool, re.Pattern | None]:
        if fullmatch(pattern_grp.server_startup_done, text) is not None:
            return True, pattern_grp.server_startup_done
        return False, None


class RconStartedEvent(LogEvent):
    def __init__(self, server_id: str, pattern: re.Pattern, data: LogInputData) -> None:
        super().__init__(server_id, data)
        self.pattern = pattern
        matched = fullmatch(self.pattern, self.log_content)
        if matched is None:
            raise ValueError(f"无法解析的服务器 RCON 客户端连接事件: {self.log_content}")

        self.rcon_started_matched = matched
        self.contents = (
            content.TextContent(f"Server {self.server_id} has started RCON."),
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(server={self.server_id!r})"

    @property
    def rcon_host(self) -> str:
        return cast(str, cast(ServerManager, self.get_origin_info().in_src).rcon_host)

    @property
    def rcon_port(self) -> int:
        return cast(ServerManager, self.get_origin_info().in_src).rcon_port

    @classmethod
    def _is_rcon_started(
        cls, pattern_grp: PatternGroup, text: str
    ) -> tuple[bool, re.Pattern | None]:
        if fullmatch(pattern_grp.rcon_started, text) is not None:
            return True, pattern_grp.rcon_started
        return False, None
