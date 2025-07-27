from __future__ import annotations

from enum import Enum

from melobot.typ import SyncOrAsyncCallable
from melobot.utils.check import Checker
from typing_extensions import TYPE_CHECKING, Iterable, Optional, cast

if TYPE_CHECKING:
    from ..adapter.event import Event, LogEvent, MessageEvent


class LevelRole(int, Enum):
    """用户权限等级枚举"""

    OWNER = 1 << 4
    SU = 1 << 3
    WHITE = 1 << 2
    NORMAL = 1 << 1
    BLACK = 1


def get_level_role(checker: MsgChecker, event: "MessageEvent") -> LevelRole:
    """获得消息事件对应的分级权限等级

    :param event: 消息事件
    :return: 分级权限等级
    """
    _this = get_level_role
    _flag = (checker.black_users, checker.owner, checker.super_users, checker.white_users)
    ret = event.flag_get(_this, _flag, raise_exc=False, default=None)
    if ret is not None:
        return cast(LevelRole, ret)

    id = event.player_name
    if id in _flag[0]:
        res = LevelRole.BLACK
    elif id == _flag[1]:
        res = LevelRole.OWNER
    elif id in _flag[2]:
        res = LevelRole.SU
    elif id in _flag[3]:
        res = LevelRole.WHITE
    else:
        res = LevelRole.NORMAL
    event.flag_set(_this, _flag, res)
    return res


class MsgChecker(Checker["Event"]):
    """消息事件分级权限检查器

    主要分 主人、超级用户、白名单用户、普通用户、黑名单用户 五级
    """

    def __init__(
        self,
        role: LevelRole,
        owner: Optional[str] = None,
        super_users: Optional[Iterable[str]] = None,
        white_users: Optional[Iterable[str]] = None,
        black_users: Optional[Iterable[str]] = None,
        fail_cb: Optional[SyncOrAsyncCallable[[], None]] = None,
    ) -> None:
        """初始化一个消息事件分级权限检查器

        :param role: 允许的等级（>= 此等级才能通过校验）
        :param owner: 主人的 id
        :param super_users: 超级用户 id
        :param white_users: 白名单用户 id
        :param black_users: 黑名单用户 id
        :param fail_cb: 检查不通过的回调
        """
        super().__init__(fail_cb)
        self.check_role = role

        self.owner = owner
        self.super_users = tuple(super_users) if super_users is not None else ()
        self.white_users = tuple(white_users) if white_users is not None else ()
        self.black_users = tuple(black_users) if black_users is not None else ()
        self._hash_tag: tuple[str | None | tuple | LevelRole, ...] = (
            self.check_role,
            self.owner,
            self.super_users,
            self.white_users,
            self.black_users,
        )

    def _check(self, event: "MessageEvent") -> bool:
        e_level = get_level_role(self, event)
        status = LevelRole.BLACK < e_level and e_level >= self.check_role
        return status

    async def check(self, event: "Event") -> bool:
        status = is_msg = False
        try:
            ret, is_msg = event.flag_get(
                self.__class__, self._hash_tag, raise_exc=False, default=(None, False)
            )
            if ret is not None:
                return cast(bool, ret)

            # 不要使用 isinstace，避免通过反射模式注入的 event 依赖产生误判结果
            if not (event.is_log() and cast("LogEvent", event).is_message()):
                status = is_msg = False
            else:
                is_msg = True
                status = self._check(cast("MessageEvent", event))

            event.flag_set(self.__class__, self._hash_tag, (status, is_msg))
            return status

        finally:
            if not status and is_msg and self.fail_cb is not None:
                await self.fail_cb()


class MsgCheckerFactory:
    """消息事件分级权限检查器的工厂

    预先存储检查依据（各等级数据），指定检查等级后，可返回一个 :class:`MsgChecker` 类的对象
    """

    def __init__(
        self,
        owner: Optional[str] = None,
        super_users: Optional[Iterable[str]] = None,
        white_users: Optional[Iterable[str]] = None,
        black_users: Optional[Iterable[str]] = None,
        white_groups: Optional[Iterable[str]] = None,
        fail_cb: Optional[SyncOrAsyncCallable[[], None]] = None,
    ) -> None:
        """初始化一个消息事件分级权限检查器的工厂

        :param owner: 主人的 id
        :param super_users: 超级用户 id
        :param white_users: 白名单用户 id
        :param black_users: 黑名单用户 id
        :param white_groups: 白名单群号（不在其中的群不通过校验）
        :param fail_cb: 检查不通过的回调（这将自动附加到生成的检查器上）
        """
        self.owner = owner
        self.super_users = tuple(super_users) if super_users is not None else ()
        self.white_users = tuple(white_users) if white_users is not None else ()
        self.black_users = tuple(black_users) if black_users is not None else ()
        self.white_groups = tuple(white_groups) if white_groups is not None else ()

        self.fail_cb = fail_cb

    def get(
        self,
        role: LevelRole,
        fail_cb: Optional[SyncOrAsyncCallable[[], None]] = None,
    ) -> MsgChecker:
        """根据内部依据和给定等级，生成一个 :class:`MsgChecker` 对象

        :param role: 允许的等级（>= 此等级才能通过校验）
        :param fail_cb: 检查不通过的回调
        :return: 消息事件分级权限检查器
        """
        return MsgChecker(
            role,
            self.owner,
            self.super_users,
            self.white_users,
            self.black_users,
            self.fail_cb if fail_cb is None else fail_cb,
        )
