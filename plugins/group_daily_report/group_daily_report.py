from datetime import datetime, time as datetime_time, timedelta
from typing import Any

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types.napcat import MessageHistory

from plugins.message_archive.message_store import (
    MessageStore,
    get_message_archive_db_path,
)


class GroupDailyReport(NcatBotPlugin):
    """生成群聊每日数据报表的插件。"""

    name = "group_daily_report"
    version = "0.1.0"
    description = "生成每日聊天数据报表"

    rank: dict[str, int]
    daily_message_total: int
    message_store: MessageStore

    async def on_load(self):
        """插件加载时连接共享消息归档数据库。"""

        self.rank = {}
        self.daily_message_total = 0
        self.message_store = MessageStore(get_message_archive_db_path(self.workspace))
        self.message_store.init()

    async def get_daily_message_rank(
        self,
        group_id: str,
        target_date: str | None = None,
        count: int = 100,
        max_count: int = 5000,
    ) -> dict[str, int]:
        """获取指定日期的群发言次数排行，并保存到 self.rank。

        Args:
            group_id: 需要统计的群号。
            target_date: 目标日期。支持 YYYY-MM-DD、今日、昨日；为空时统计昨日。
            count: 每批请求群历史消息的数量。
            max_count: 最多合并的历史消息数量，用于限制分页拉取范围。

        Returns:
            按发言次数降序排列的字典。键为用户 QQ 号，值为发言次数。
        """

        day = self._resolve_target_date(target_date)

        # 用当天的完整时间边界过滤历史消息和数据库统计范围。
        start_timestamp = int(datetime.combine(day, datetime_time.min).timestamp())
        end_timestamp = int(datetime.combine(day, datetime_time.max).timestamp())

        # 生成日报前先补拉历史消息，确保 Bot 离线或插件未加载期间的消息也能入库。
        await self._get_group_history_messages(
            group_id=group_id,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            batch_size=count,
            max_count=max_count,
        )

        self.daily_message_total = self.message_store.count_group_messages(
            group_id,
            start_timestamp,
            end_timestamp,
        )
        self.rank = self.message_store.get_group_message_rank(
            group_id,
            start_timestamp,
            end_timestamp,
        )
        return self.rank

    @registrar.qq.on_group_command("#每日报表")
    async def generate_daily_report(
        self,
        event: GroupMessageEvent,
        date: str | None = None,
    ):
        """处理 #每日报表 群命令，并回复发言次数排行。

        Args:
            event: 触发命令的群消息事件。
            date: 可选目标日期。支持 YYYY-MM-DD、今日、昨日；为空时统计昨日。

        Returns:
            本次统计得到的发言次数排行字典。
        """

        try:
            day = self._resolve_target_date(date)
            rank = await self.get_daily_message_rank(str(event.group_id), date)
        except ValueError:
            await event.reply("日期格式错误喵，请使用“YYYY-MM-DD”的日期格式，或直接输入“今日”或“昨日”喵！")
            return {}

        if not rank:
            await event.reply(f"{day:%Y-%m-%d} 暂无聊天记录喵")
            return rank

        lines = [
            "\n"
            f"{day:%Y-%m-%d} 当日发送消息总数：{self.daily_message_total}",
            "发言次数排行：",
        ]
        for index, (user_id, message_count) in enumerate(
            list(rank.items())[:10],
            start=1,
        ):
            # self.rank 保留 user_id；发送日报时再转换为群内展示名。
            display_name = await self._get_group_display_name(
                str(event.group_id),
                user_id,
            )
            lines.append(f"{index}. {display_name}: {message_count}")

        await event.reply("\n".join(lines))
        return rank

    async def _get_group_history_messages(
        self,
        group_id: str,
        start_timestamp: int,
        end_timestamp: int,
        batch_size: int = 100,
        max_count: int = 5000,
    ) -> tuple[list[Any], int]:
        """分页获取覆盖指定开始时间的群历史消息，并把拉到的消息补写入库。

        从最近一批群消息开始获取；如果当前批次最早消息仍晚于 start_timestamp，
        则使用该最早消息的游标继续向更早的历史记录翻页。

        Args:
            group_id: 需要获取历史消息的群号。
            start_timestamp: 需要覆盖到的起始时间戳。
            end_timestamp: 需要统计的结束时间戳。
            batch_size: 每次请求的消息数量。
            max_count: 最多合并的消息数量。

        Returns:
            二元组。第一项为已获取并按消息 ID 去重后的历史消息列表；
            第二项为数据库中目标时间范围内的消息总数。
        """

        messages: list[Any] = []
        seen_message_ids: set[str] = set()
        message_seq: str | None = None
        batch_size = max(1, int(batch_size))
        max_count = max(1, int(max_count))

        while len(messages) < max_count:
            request_count = min(batch_size, max_count - len(messages))
            request_params: dict[str, Any] = {
                "group_id": group_id,
                "count": request_count,
            }
            if message_seq is not None:
                request_params["message_seq"] = message_seq
                request_params["reverse_order"] = True

            chat_history_result = await self._request_group_msg_history(
                **request_params
            )
            batch_messages = list(getattr(chat_history_result, "messages", []) or [])

            if not batch_messages:
                break

            self.message_store.save_group_messages(group_id, batch_messages)

            # 每条消息先生成身份标识；已记录过的标识直接跳过，避免分页重叠导致重复统计。
            for message in batch_messages:
                message_identity = self._message_identity(message)
                if message_identity is None:
                    messages.append(message)
                    continue
                if message_identity in seen_message_ids:
                    continue
                seen_message_ids.add(message_identity)
                messages.append(message)

            earliest_message = self._earliest_message(batch_messages)
            if earliest_message is None:
                break

            # 当前批次已经覆盖到目标日期零点，剩余精确范围交给数据库时间过滤处理。
            if self._message_time(earliest_message) <= start_timestamp:
                break

            next_message_seq = self._message_cursor(earliest_message)
            # 没有可用游标或游标未前进时停止，避免接口异常时陷入死循环。
            if next_message_seq is None or next_message_seq == message_seq:
                break
            message_seq = next_message_seq

        total_messages = self.message_store.count_group_messages(
            group_id,
            start_timestamp,
            end_timestamp,
        )
        return messages, total_messages

    async def _request_group_msg_history(
        self,
        group_id: str,
        count: int,
        message_seq: str | None = None,
        reverse_order: bool = False,
    ) -> MessageHistory:
        """请求群历史消息，并支持 NapCat 的反向分页参数。

        Args:
            group_id: 需要获取历史消息的群号。
            count: 本次请求的消息数量。
            message_seq: 起始消息序号；为空时获取最新消息。
            reverse_order: 是否从起始消息向更早方向获取。

        Returns:
            NcatBot 历史消息响应对象。
        """

        params: dict[str, Any] = {
            "group_id": int(group_id),
            "count": int(count),
        }
        if message_seq is not None:
            params["message_seq"] = int(message_seq)
        if reverse_order:
            params["reverse_order"] = True

        data = await self.api.qq._api._call_data(
            "get_group_msg_history",
            params,
        ) or {}
        return MessageHistory(**data)

    @staticmethod
    def _resolve_target_date(target_date: str | None):
        """解析日报统计日期。

        Args:
            target_date: 用户输入的日期参数。支持 YYYY-MM-DD、今日、昨日；为空时表示昨日。

        Returns:
            解析后的日期对象。

        Raises:
            ValueError: 日期参数不是支持的格式。
        """

        today = datetime.now().date()
        if target_date is None or not target_date.strip():
            return today - timedelta(days=1)

        normalized_date = target_date.strip()
        if normalized_date == "今日":
            return today
        if normalized_date == "昨日":
            return today - timedelta(days=1)

        return datetime.strptime(normalized_date, "%Y-%m-%d").date()

    @staticmethod
    def _message_time(message: Any) -> int:
        """获取历史消息对象中的发送时间戳。

        Args:
            message: NcatBot 返回的历史消息对象。

        Returns:
            消息发送时间戳；当消息缺少时间字段时返回 0。
        """

        return int(getattr(message, "time", 0) or 0)

    @classmethod
    def _earliest_message(cls, messages: list[Any]) -> Any | None:
        """获取一批历史消息中时间最早的消息。

        Args:
            messages: NcatBot 返回的一批历史消息对象。

        Returns:
            时间戳最小的消息对象；当所有消息都缺少有效时间戳时返回 None。
        """

        valid_messages = [
            message
            for message in messages
            if cls._message_time(message) > 0
        ]
        if not valid_messages:
            return None
        return min(valid_messages, key=cls._message_time)

    @staticmethod
    def _message_identity(message: Any) -> str | None:
        """获取用于历史消息去重的消息身份标识。

        Args:
            message: NcatBot 返回的历史消息对象。

        Returns:
            形如 message_id:xxx 或 real_id:xxx 的消息身份标识；
            当消息缺少 message_id 和 real_id 时返回 None。
        """

        message_id = getattr(message, "message_id", None)
        if message_id:
            return f"message_id:{message_id}"

        real_id = getattr(message, "real_id", None)
        if real_id is not None:
            return f"real_id:{real_id}"

        return None

    @staticmethod
    def _message_cursor(message: Any) -> str | None:
        """获取继续向前分页所需的消息游标。

        Args:
            message: 当前批次中时间最早的历史消息对象。

        Returns:
            可传给 get_group_msg_history 的 message_seq；缺少可用游标时返回 None。
        """

        for field_name in ("message_seq", "message_id", "real_id"):
            field_value = getattr(message, field_name, None)
            if field_value is None:
                continue

            field_text = str(field_value).strip()
            if field_text.isdigit():
                return field_text

        return None

    async def _get_group_display_name(self, group_id: str, user_id: str) -> str:
        """获取用户在指定群内的展示名称。

        优先使用数据库里实时入库保存的群名片；没有时查询群成员接口；
        群名片为空时使用 QQ 昵称；查询失败时回退为用户 QQ 号。

        Args:
            group_id: 群号。
            user_id: 用户 QQ 号。

        Returns:
            用户在群内应展示的名称。
        """

        stored_name = self.message_store.get_group_display_name(group_id, user_id)
        if stored_name:
            return stored_name

        try:
            member_info = await self.api.qq.query.get_group_member_info(
                group_id=group_id,
                user_id=user_id,
            )
        except Exception:
            return user_id

        if not member_info:
            return user_id

        card = getattr(member_info, "card", None)
        nickname = getattr(member_info, "nickname", None)
        return card or nickname or user_id
