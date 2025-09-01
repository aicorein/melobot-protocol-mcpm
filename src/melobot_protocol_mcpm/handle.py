from melobot.handle import FlowDecorator
from melobot.session import DefaultRule, Rule
from melobot.typ import SyncOrAsyncCallable
from melobot.utils.check import Checker, checker_join
from melobot.utils.match import Matcher
from melobot.utils.parse import Parser
from typing_extensions import Callable, Literal, Sequence

from .adapter.event import (
    Event,
    LogEvent,
    MessageEvent,
    PlayerEvent,
    RconStartedEvent,
    ServerDoneEvent,
    StderrEvent,
    StdoutEvent,
)


def on_event(
    checker: Checker | None | SyncOrAsyncCallable[[Event], bool] = None,
    priority: int = 0,
    block: bool = False,
    temp: bool = False,
    decos: Sequence[Callable[[Callable], Callable]] | None = None,
    rule: Rule[Event] | None = None,
) -> FlowDecorator:
    return FlowDecorator(
        checker=checker_join(lambda e: isinstance(e, Event), checker),  # type: ignore[arg-type]
        priority=priority,
        block=block,
        temp=temp,
        decos=decos,
        rule=rule,  # type: ignore[arg-type]
    )


def on_log(
    checker: Checker | None | SyncOrAsyncCallable[[LogEvent], bool] = None,
    matcher: Matcher | None = None,
    parser: Parser | None = None,
    priority: int = 0,
    block: bool = False,
    temp: bool = False,
    decos: Sequence[Callable[[Callable], Callable]] | None = None,
    rule: Rule[Event] | None = None,
) -> FlowDecorator:
    return FlowDecorator(
        checker=checker_join(lambda e: isinstance(e, LogEvent), checker),  # type: ignore[arg-type]
        matcher=matcher,
        parser=parser,
        priority=priority,
        block=block,
        temp=temp,
        decos=decos,
        rule=rule,  # type: ignore[arg-type]
    )


def on_stdout(
    checker: Checker | None | SyncOrAsyncCallable[[StdoutEvent], bool] = None,
    matcher: Matcher | None = None,
    parser: Parser | None = None,
    priority: int = 0,
    block: bool = False,
    temp: bool = False,
    decos: Sequence[Callable[[Callable], Callable]] | None = None,
    rule: Rule[Event] | None = None,
) -> FlowDecorator:
    return FlowDecorator(
        checker=checker_join(lambda e: isinstance(e, StdoutEvent), checker),  # type: ignore[arg-type]
        matcher=matcher,
        parser=parser,
        priority=priority,
        block=block,
        temp=temp,
        decos=decos,
        rule=rule,  # type: ignore[arg-type]
    )


def on_stderr(
    checker: Checker | None | SyncOrAsyncCallable[[StderrEvent], bool] = None,
    matcher: Matcher | None = None,
    parser: Parser | None = None,
    priority: int = 0,
    block: bool = False,
    temp: bool = False,
    decos: Sequence[Callable[[Callable], Callable]] | None = None,
    rule: Rule[Event] | None = None,
) -> FlowDecorator:
    return FlowDecorator(
        checker=checker_join(lambda e: isinstance(e, StderrEvent), checker),  # type: ignore[arg-type]
        matcher=matcher,
        parser=parser,
        priority=priority,
        block=block,
        temp=temp,
        decos=decos,
        rule=rule,  # type: ignore[arg-type]
    )


def on_message(
    checker: Checker | None | SyncOrAsyncCallable[[MessageEvent], bool] = None,
    matcher: Matcher | None = None,
    parser: Parser | None = None,
    priority: int = 0,
    block: bool = False,
    temp: bool = False,
    decos: Sequence[Callable[[Callable], Callable]] | None = None,
    legacy_session: bool = False,
) -> FlowDecorator:
    return FlowDecorator(
        checker=checker_join(lambda e: isinstance(e, MessageEvent), checker),  # type: ignore[arg-type]
        matcher=matcher,
        parser=parser,
        priority=priority,
        block=block,
        temp=temp,
        decos=decos,
        rule=DefaultRule() if legacy_session else None,
    )


def on_player_operation(
    type: Literal["joined", "left", "all"],
    checker: Checker | None | SyncOrAsyncCallable[[PlayerEvent], bool] = None,
    priority: int = 0,
    block: bool = False,
    temp: bool = False,
    decos: Sequence[Callable[[Callable], Callable]] | None = None,
    rule: Rule[Event] | None = None,
) -> FlowDecorator:
    return FlowDecorator(
        checker=checker_join(lambda e: isinstance(e, PlayerEvent) and (type == "all" or e.operation_type == type), checker),  # type: ignore[arg-type]
        priority=priority,
        block=block,
        temp=temp,
        decos=decos,
        rule=rule,  # type: ignore[arg-type]
    )


def on_server_done(
    checker: Checker | None | SyncOrAsyncCallable[[ServerDoneEvent], bool] = None,
    priority: int = 0,
    block: bool = False,
    temp: bool = False,
    decos: Sequence[Callable[[Callable], Callable]] | None = None,
    rule: Rule[Event] | None = None,
) -> FlowDecorator:
    return FlowDecorator(
        checker=checker_join(lambda e: isinstance(e, ServerDoneEvent), checker),  # type: ignore[arg-type]
        priority=priority,
        block=block,
        temp=temp,
        decos=decos,
        rule=rule,  # type: ignore[arg-type]
    )


def on_rcon_started(
    checker: Checker | None | SyncOrAsyncCallable[[RconStartedEvent], bool] = None,
    priority: int = 0,
    block: bool = False,
    temp: bool = False,
    decos: Sequence[Callable[[Callable], Callable]] | None = None,
    rule: Rule[Event] | None = None,
) -> FlowDecorator:
    return FlowDecorator(
        checker=checker_join(lambda e: isinstance(e, RconStartedEvent), checker),  # type: ignore[arg-type]
        priority=priority,
        block=block,
        temp=temp,
        decos=decos,
        rule=rule,  # type: ignore[arg-type]
    )
