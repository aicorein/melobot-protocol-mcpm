from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from ..adapter.action import (
        CmdAction,
        RawCmdStrAction,
        SendBroadcastMsgAction,
        SendMsgAction,
    )


class CmdFactory:
    async def create_cmd(self, action: "CmdAction") -> str:
        return f"{action.cmd_name} {' '.join(map(str, action.cmd_args))}"

    async def create_raw_cmd(self, action: "RawCmdStrAction") -> str:
        return action.cmd

    async def create_send_msg(self, action: "SendMsgAction") -> str:
        if isinstance(action.message, str):
            return f'tellraw {action.target} \"{action.message}\"'
        else:
            raise ValueError("暂不支持的消息格式")

    async def create_send_broadcast_msg(self, action: "SendBroadcastMsgAction") -> str:
        return await self.create_send_msg(action)
