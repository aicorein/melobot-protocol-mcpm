from __future__ import annotations

from melobot.adapter import Echo as RootEcho
from typing_extensions import Any, Generic, cast

from ..const import PROTOCOL_IDENTIFIER
from ..io.model import CmdEchoData, EchoDataT, EchoType
from ..utils.common import truncate


class Echo(RootEcho, Generic[EchoDataT]):
    def __init__(self, data: EchoDataT) -> None:
        super().__init__(protocol=PROTOCOL_IDENTIFIER)
        self.type = data.type
        self.raw = data
        self.content = data.content

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.type})"

    def result(self) -> Any:
        if self.content is None:
            raise ValueError("回应中的响应内容为空")
        return self.content

    @classmethod
    def resolve(cls, data: EchoDataT) -> Echo:
        match data.type:
            case EchoType.CMD_RESP:
                return CmdEcho(cast(CmdEchoData, data))
            case _:
                return cls(data)


class CmdEcho(Echo[CmdEchoData]):
    def __init__(self, data: CmdEchoData) -> None:
        super().__init__(data)
        self.cmd = data.cmd
        self.content: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(ret={truncate(self.content, 100)!r})"

    def result(self) -> str:
        if self.content in (None, ""):
            raise ValueError("回应中的响应内容为空或空字符串")
        return self.content
