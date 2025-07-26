from melobot.adapter import (
    AbstractEchoFactory,
    AbstractEventFactory,
    AbstractOutputFactory,
    ActionHandleGroup
)
from melobot.adapter import Adapter as RootAdapter
from typing_extensions import Sequence, cast
from melobot.handle import try_get_event

from ..const import PROTOCOL_IDENTIFIER
from ..io.manager import ServerManager
from ..io.model import CmdOutputData, EchoPacket, InPacket, OutPacket, OutputType
from ..utils.cmd import CmdFactory
from ..utils.text import JsonText
from . import action as ac
from . import echo as ec
from . import event as ev


class EventFactory(AbstractEventFactory[InPacket, ev.Event]):
    async def create(self, packet: InPacket) -> ev.Event:
        return ev.Event.resolve(packet.server_id, packet.data)


class OutputFactory(AbstractOutputFactory[OutPacket, ac.Action]):
    cmd_factory = CmdFactory()

    async def create(self, action: ac.Action) -> OutPacket:
        match action.type:
            case OutputType.CMD:
                action = cast(ac.CmdAction, action)
                cmd_str = await ac.create_cmd_str(action, self.cmd_factory)
                return OutPacket(data=CmdOutputData(content=cmd_str))
            case _:
                raise ValueError(f"不支持的行为操作：{action}")


class EchoFactory(AbstractEchoFactory[EchoPacket, ec.Echo]):
    async def create(self, packet: EchoPacket) -> ec.Echo | None:
        if packet.noecho:
            return None
        return ec.Echo.resolve(packet.data)


class Adapter(
    RootAdapter[
        EventFactory, OutputFactory, EchoFactory, ac.Action, ServerManager, ServerManager
    ]
):
    def __init__(self) -> None:
        super().__init__(
            PROTOCOL_IDENTIFIER, EventFactory(), OutputFactory(), EchoFactory()
        )

    async def __send_text__(self, text: str) -> ActionHandleGroup[ec.CmdEcho]:
        return await self.send_msg(None, text)

    async def send_msg(
        self, target: str | None, message: str | JsonText | Sequence[str] | Sequence[JsonText]
    ) -> ActionHandleGroup[ec.CmdEcho]:
        if target is None:
            event = try_get_event()
            if isinstance(event, (ev.MessageEvent, ev.PlayerEvent)):
                target = event.player_name
            else:
                raise ValueError("当前上下文的事件，没有玩家名称信息，无法自动定位消息发送目标")
        return await self.call_output(ac.SendMsgAction(target, message))

    async def send_broadcast_msg(
        self, message: str | JsonText | Sequence[str] | Sequence[JsonText]
    ) -> ActionHandleGroup[ec.CmdEcho]:
        return await self.call_output(ac.SendBroadcastMsgAction(message))

    async def send_cmd(self, cmd: str) -> ActionHandleGroup[ec.CmdEcho]:
        return await self.call_output(ac.RawCmdStrAction(cmd))
