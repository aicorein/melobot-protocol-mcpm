from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from melobot.io import EchoPacket as RootEchoPak
from melobot.io import InPacket as RootInPak
from melobot.io import OutPacket as RootOutPak
from typing_extensions import TYPE_CHECKING, Any, Literal, TypeVar

from ..const import PROTOCOL_IDENTIFIER
from ..utils.cmd import CmdFactory
from ..utils.pattern import RegexPatternGroup

if TYPE_CHECKING:
    from ..adapter.action import CmdAction


@dataclass(kw_only=True)
class InPacket(RootInPak):  # type: ignore[override]
    server_id: str
    data: InputData
    protocol: str = PROTOCOL_IDENTIFIER


@dataclass(kw_only=True)
class OutPacket(RootOutPak):  # type: ignore[override]
    data: OutputData
    protocol: str = PROTOCOL_IDENTIFIER


@dataclass(kw_only=True)
class EchoPacket(RootEchoPak):  # type: ignore[override]
    data: EchoData
    protocol: str = PROTOCOL_IDENTIFIER


class InputType(Enum):
    LOG = "log"


class OutputType(Enum):
    CMD = "cmd"


class EchoType(Enum):
    CMD_RESP = "cmd_resp"


@dataclass(kw_only=True, frozen=True)
class InputData:
    type: InputType
    content: Any


InputDataT = TypeVar("InputDataT", bound=InputData)


@dataclass(kw_only=True, frozen=True)
class LogInputData(InputData):
    type: Literal[InputType.LOG] = InputType.LOG
    content: str
    pattern_group: RegexPatternGroup
    cmd_factory: CmdFactory


@dataclass(kw_only=True, frozen=True)
class OutputData:
    type: OutputType
    content: Any


OutputDataT = TypeVar("OutputDataT", bound=OutputData)


@dataclass(kw_only=True, frozen=True)
class CmdOutputData(OutputData):
    type: Literal[OutputType.CMD] = OutputType.CMD
    content: "CmdAction"


@dataclass(kw_only=True, frozen=True)
class EchoData:
    type: EchoType
    content: Any


EchoDataT = TypeVar("EchoDataT", bound=EchoData)


@dataclass(kw_only=True, frozen=True)
class CmdEchoData(EchoData):
    type: Literal[EchoType.CMD_RESP] = EchoType.CMD_RESP
    content: str
    cmd: str
