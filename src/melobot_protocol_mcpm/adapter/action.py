from melobot.adapter import Action as RootAction
from melobot.handle import try_get_event
from typing_extensions import Any, Sequence

from ..const import PROTOCOL_IDENTIFIER
from ..io.model import OutputType
from ..utils.cmd import CmdFactory
from ..utils.text import JsonText


class Action(RootAction):
    def __init__(self, type: OutputType) -> None:
        self.type = type
        super().__init__(
            protocol=PROTOCOL_IDENTIFIER,
            trigger=try_get_event(),
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.type._name_})"


class CmdAction(Action):
    def __init__(self, cmd_name: str, *args: Any) -> None:
        super().__init__(OutputType.CMD)
        self.cmd_name = cmd_name
        self.cmd_args = args

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cmd_name={self.cmd_name!r}, args:{len(self.cmd_args)})"


class RawCmdStrAction(CmdAction):
    def __init__(self, cmd_str: str) -> None:
        super().__init__(*cmd_str.split(" ", maxsplit=1))
        self.cmd = cmd_str


class SendMsgAction(CmdAction):
    def __init__(
        self, target: str, message: str | JsonText | Sequence[str] | Sequence[JsonText]
    ) -> None:
        super().__init__("tellraw", target, message)
        self.target = target
        self.message = message


class SendBroadcastMsgAction(SendMsgAction):
    def __init__(
        self, message: str | JsonText | Sequence[str] | Sequence[JsonText]
    ) -> None:
        super().__init__("@a", message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cmd_name={self.cmd_name!r}, target=@a, args: {len(self.cmd_args)})"


async def create_cmd_str(action: CmdAction, factory: CmdFactory) -> str:
    match action:
        case SendMsgAction():
            return await factory.create_send_msg(action)
        case SendBroadcastMsgAction():
            return await factory.create_send_broadcast_msg(action)
        case RawCmdStrAction():
            return await factory.create_raw_cmd(action)
        case _:
            return await factory.create_cmd(action)
