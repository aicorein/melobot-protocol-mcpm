from melobot.protocols import ProtocolStack

from .adapter import *  # noqa: F403
from .const import PROTOCOL_IDENTIFIER, PROTOCOL_NAME, PROTOCOL_SUPPORT_AUTHOR, PROTOCOL_VERSION
from .handle import (
    on_event,
    on_log,
    on_message,
    on_player_operation,
    on_rcon_started,
    on_server_done,
    on_stderr,
    on_stdout,
)
from .io import *  # noqa: F403
from .utils import *  # noqa: F403


class MCPMProtocol(ProtocolStack):
    def __init__(self, *srcs: ServerManager) -> None:
        super().__init__()
        self.adapter = Adapter()
        self.inputs = set()
        self.outputs = set()

        for src in srcs:
            if not isinstance(src, ServerManager):
                raise TypeError(
                    f"不支持的 MCPM 源类型（不是有效的 {ServerManager.__class__.__name__} 对象）: {type(src)}"
                )
            if isinstance(src, ServerManager):
                self.inputs.add(src)
            if isinstance(src, ServerManager):
                self.outputs.add(src)
