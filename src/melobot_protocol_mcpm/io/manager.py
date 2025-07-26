from __future__ import annotations

import asyncio
import asyncio.subprocess
from pathlib import Path
from weakref import WeakValueDictionary

from aiomcrcon import Client as RconClient
from melobot import get_bot
from melobot.io import AbstractIOSource
from melobot.log import LogLevel, logger
from typing_extensions import Any, ClassVar, Mapping, Sequence, cast

from ..const import PROTOCOL_IDENTIFIER
from ..utils.cmd import CmdFactory
from ..utils.common import truncate
from ..utils.pattern import RegexPatternGroup
from .model import (
    CmdEchoData,
    CmdOutputData,
    EchoPacket,
    InPacket,
    LogInputData,
    OutPacket,
)


class ServerManager(AbstractIOSource[InPacket, OutPacket, EchoPacket]):
    __instances__: ClassVar[WeakValueDictionary[str, ServerManager]] = (
        WeakValueDictionary()
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"

    def __init__(
        self,
        name: str,
        java_exec: str | Path | None = None,
        jar_path: str | Path | None = None,
        jvm_flags: str | Sequence[str] = "",
        postfix_args: str | Sequence[str] = "",
        run_cmd: str | None = None,
        work_path: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        extra_exec_args: dict[str, Any] | None = None,
        pattern_group: RegexPatternGroup | None = None,
        cmd_factory: CmdFactory | None = None,
        rcon_host: str | None = None,
        rcon_port: int = 25575,
        rcon_password: str = "",
        rcon_init_timeout: int = 10,
        rcon_cmd_timeout: int = 5,
        encoding: str = "utf-8",
        decoding: str = "utf-8",
        to_console: bool = False,
    ) -> None:
        super().__init__()
        self.protocol = PROTOCOL_IDENTIFIER
        self.name = name
        if self.name in self.__instances__:
            raise ValueError(f"已有同名的服务端管理器: {self}")
        self.__instances__[self.name] = self

        if run_cmd is None:
            java_exec = Path(cast(str | Path, java_exec)).resolve(strict=True)
            jar_path = Path(cast(str | Path, jar_path)).resolve(strict=True)
            jvm_flags = self._normalize_args(jvm_flags)
            postfix_args = self._normalize_args(postfix_args)
            self.exec_cmd = f"{java_exec} {jvm_flags} -jar {jar_path} {postfix_args}"
        else:
            self.exec_cmd = run_cmd

        self.pattern_group = (
            pattern_group if pattern_group is not None else RegexPatternGroup()
        )
        self.cmd_factory = cmd_factory if cmd_factory is not None else CmdFactory()

        self.rcon_host = rcon_host
        self.rcon_port = rcon_port
        self.rcon_password = rcon_password
        self.rcon_init_timeout = rcon_init_timeout
        self.rcon_cmd_timeout = rcon_cmd_timeout
        self.rcon_client: RconClient
        self.encoding = encoding
        self.decoding = decoding
        self.to_console = to_console

        if work_path is not None:
            self.work_path = Path(work_path).resolve(strict=True)
        else:
            self.work_path = Path.cwd().resolve()
        self.env = env
        self.extra_exec_args = extra_exec_args if extra_exec_args is not None else {}

        self.proc: asyncio.subprocess.Process
        self.proc_ret: int | None = None

        self._lock = asyncio.Lock()
        self._opened = asyncio.Event()
        self._tasks: set[asyncio.Task[None]] = set()
        self._in_buf: asyncio.Queue[str] = asyncio.Queue()
        self._out_buf: asyncio.Queue[tuple[str, asyncio.Future[str]]] = asyncio.Queue()
        self._server_done = asyncio.Event()

    def _normalize_args(self, args: str | Sequence[str]) -> str:
        if isinstance(args, str):
            return args
        return " ".join(args)

    async def open(self) -> None:
        if self._opened.is_set():
            return

        async with self._lock:
            if self._opened.is_set():
                return

            self._server_done.clear()

            if self.rcon_host is None:
                logger.warning("RCON 功能未启用，mcpm 协议的所有操作都将产生空回应")
            self.rcon_client = RconClient(
                self.rcon_host, self.rcon_port, self.rcon_password
            )
            self._tasks.add(asyncio.create_task(self._proc_stdout_worker()))
            self._tasks.add(asyncio.create_task(self._proc_stderr_worker()))
            self._tasks.add(asyncio.create_task(self._proc_input_worker()))

            self.proc_ret = None
            try:
                self.proc = await asyncio.create_subprocess_exec(
                    *self.exec_cmd.split(),
                    cwd=str(self.work_path),
                    env=self.env,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    **self.extra_exec_args,
                )
                if not all((self.proc.stdin, self.proc.stdout, self.proc.stderr)):
                    raise RuntimeError(f"创建服务端 {self.name} 进程失败（{self.proc}）")
            except Exception as e:
                logger.error(f"Minecraft 服务端 {self.name} 启动失败: {e}")
                raise
            else:
                logger.info(f"Minecraft 服务端 {self.name} 已启动")

            self._opened.set()
            logger.info(f"Minecraft 服务端 {self.name} 的管理器已开始运行")

    def opened(self) -> bool:
        return self._opened.is_set()

    async def close(self) -> None:
        if not self._opened.is_set():
            return

        async with self._lock:
            if not self._opened.is_set():
                return

            self._opened.clear()
            self.proc.terminate()
            for t in self._tasks:
                t.cancel()
            self.proc_ret = await self.proc.wait()
            await asyncio.wait(self._tasks)
            del self.proc
            logger.info(
                f"Minecraft 服务端 {self.name} 进程已退出，返回码：{self.proc_ret}"
            )

            self._in_buf = asyncio.Queue()
            self._out_buf = asyncio.Queue()
            logger.info(f"Minecraft 服务端 {self.name} 的 IO 缓存已清空")
            logger.info(f"Minecraft 服务端 {self.name} 的管理器已停止运行")

    async def input(self) -> InPacket:
        await self._opened.wait()
        in_str = await self._in_buf.get()
        if self.to_console:
            logger.generic_lazy(
                "%s",
                lambda: f"服务端 {self.name} 输出: {truncate(in_str)}",
                level=LogLevel.DEBUG,
            )
        return InPacket(
            data=LogInputData(
                content=in_str,
                pattern_group=self.pattern_group,
                cmd_factory=self.cmd_factory,
            ),
            server_id=self.name,
        )

    async def output(self, packet: OutPacket) -> EchoPacket:
        await self._opened.wait()
        out_data = packet.data
        out_data = cast(CmdOutputData, out_data)
        fut: asyncio.Future[str] = asyncio.get_running_loop().create_future()
        cmd = out_data.content
        self._out_buf.put_nowait((cmd, fut))
        logger.generic_lazy(
            "%s",
            lambda: f"服务端 {self.name} 命令（{packet.id}）: {truncate(cmd)}",
            level=LogLevel.DEBUG,
        )

        if self.rcon_host is not None:
            ret = await fut
            logger.generic_lazy(
                "%s",
                lambda: f"服务端 {self.name} 回应（{packet.id}）: {truncate(ret)}",
                level=LogLevel.DEBUG,
            )
            return EchoPacket(data=CmdEchoData(content=ret, cmd=cmd))
        else:
            return EchoPacket(data=CmdEchoData(content="", cmd=cmd), noecho=True)

    async def _proc_stdout_worker(self) -> None:
        await self._opened.wait()
        try:
            reader = cast(asyncio.StreamReader, self.proc.stdout)
            while True:
                line_b = await reader.readline()
                line = line_b.decode(self.decoding).strip("\n")
                self._in_buf.put_nowait(line)
        finally:
            logger.info("服务端 stdout 控制例程已停止")

    async def _proc_stderr_worker(self) -> None:
        await self._opened.wait()
        try:
            reader = cast(asyncio.StreamReader, self.proc.stderr)
            while True:
                line_b = await reader.readline()
                line = line_b.decode(self.decoding).strip("\n")
                self._in_buf.put_nowait(line)
        finally:
            logger.info("服务端 stderr 控制例程已停止")

    async def _proc_input_worker(self) -> None:
        await self._opened.wait()
        writer = cast(asyncio.StreamWriter, self.proc.stdin)

        from ..handle import on_rcon_started

        get_bot()._dispatcher.add(on_rcon_started(temp=True)(self._server_done.set))
        await self._server_done.wait()
        logger.info("服务端已经启动完成")
        try:
            if self.rcon_host is not None:
                await self.rcon_client.connect(timeout=self.rcon_init_timeout)
                logger.info(
                    f"RCON 客户端已连接到 {self.rcon_host}:{self.rcon_port}，对应服务端 {self.name}"
                )

            while True:
                cmd, fut = await self._out_buf.get()
                if self.rcon_host is not None:
                    ret_tup = await self.rcon_client.send_cmd(
                        cmd, timeout=self.rcon_cmd_timeout
                    )
                    res = ret_tup[0]
                    fut.set_result(res)
                else:
                    line_b = f"{cmd}\n".encode(self.encoding)
                    writer.write(line_b)
                    await writer.drain()
                    fut.set_result("")

        except Exception as e:
            logger.exception(f"服务端 stdin 控制例程运行时发生错误：{e}")

        finally:
            if self.rcon_host is not None:
                await self.rcon_client.close()
                logger.info(
                    f"连接到 {self.rcon_host}:{self.rcon_port} 的 RCON 客户端已关闭，对应服务端 {self.name}"
                )
                del self.rcon_client
                logger.info("服务端 stdin 控制例程已停止")
