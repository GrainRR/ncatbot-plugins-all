"""消息归档插件的 SQLite 存储。"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


MESSAGE_ARCHIVE_DIR_NAME = "message_archive"
MESSAGE_DB_FILENAME = "messages.sqlite"


def get_message_archive_db_path(plugin_workspace: Path) -> Path:
    """根据任意插件 workspace 获取共享消息数据库路径。

    Args:
        plugin_workspace: 当前插件的 workspace 路径，通常为 data/<插件名>。

    Returns:
        共享消息归档数据库路径 data/message_archive/messages.sqlite。
    """

    return Path(plugin_workspace).parent / MESSAGE_ARCHIVE_DIR_NAME / MESSAGE_DB_FILENAME


class MessageStore:
    """负责消息归档和统计查询的 SQLite 存储类。"""

    def __init__(self, db_path: Path) -> None:
        """创建消息存储对象。

        Args:
            db_path: SQLite 数据库文件路径。
        """

        self.db_path = Path(db_path)

    def init(self) -> None:
        """初始化数据库目录、数据库文件、数据表和统计索引。"""

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS group_messages (
                    group_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    real_id TEXT,
                    message_type TEXT,
                    time INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    sender_nickname TEXT,
                    sender_card TEXT,
                    sender_role TEXT,
                    raw_message TEXT,
                    message_segments_json TEXT,
                    message_json TEXT,
                    PRIMARY KEY (group_id, message_id)
                );

                CREATE INDEX IF NOT EXISTS idx_group_messages_group_time
                ON group_messages(group_id, time);

                CREATE INDEX IF NOT EXISTS idx_group_messages_group_time_user
                ON group_messages(group_id, time, user_id);

                CREATE TABLE IF NOT EXISTS private_messages (
                    peer_user_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    real_id TEXT,
                    message_type TEXT,
                    time INTEGER NOT NULL,
                    sender_user_id TEXT NOT NULL,
                    sender_nickname TEXT,
                    raw_message TEXT,
                    message_segments_json TEXT,
                    message_json TEXT,
                    PRIMARY KEY (peer_user_id, message_id)
                );

                CREATE INDEX IF NOT EXISTS idx_private_messages_peer_time
                ON private_messages(peer_user_id, time);

                CREATE INDEX IF NOT EXISTS idx_private_messages_peer_time_sender
                ON private_messages(peer_user_id, time, sender_user_id);
                """
            )

    def save_group_message_from_event(self, event: Any) -> bool:
        """保存实时收到的群消息事件。

        Args:
            event: NcatBot 的 GroupMessageEvent 对象。

        Returns:
            消息成功写入或更新时返回 True；缺少消息 ID 时返回 False。
        """

        return self._save_group_record(
            {
                "group_id": self._text(self._field(event, "group_id")),
                "message_id": self._text(self._field(event, "message_id")),
                "real_id": self._text(self._field(event, "real_id")),
                "message_type": self._text(self._field(event, "message_type")),
                "time": self._int(self._field(event, "time")),
                "user_id": self._message_user_id(event),
                "sender_nickname": self._sender_text(event, "nickname"),
                "sender_card": self._sender_text(event, "card"),
                "sender_role": self._sender_text(event, "role"),
                "raw_message": self._text(self._field(event, "raw_message")),
                "message_segments_json": self._message_segments_json(event),
                "message_json": self._object_json(self._field(event, "data", event)),
            }
        )

    def save_private_message_from_event(self, event: Any) -> bool:
        """保存实时收到的私聊消息事件。

        Args:
            event: NcatBot 的 PrivateMessageEvent 对象。

        Returns:
            消息成功写入或更新时返回 True；缺少消息 ID 时返回 False。
        """

        peer_user_id = self._text(self._field(event, "user_id"))
        return self._save_private_record(
            {
                "peer_user_id": peer_user_id,
                "message_id": self._text(self._field(event, "message_id")),
                "real_id": self._text(self._field(event, "real_id")),
                "message_type": self._text(self._field(event, "message_type")),
                "time": self._int(self._field(event, "time")),
                "sender_user_id": self._message_user_id(event),
                "sender_nickname": self._sender_text(event, "nickname"),
                "raw_message": self._text(self._field(event, "raw_message")),
                "message_segments_json": self._message_segments_json(event),
                "message_json": self._object_json(self._field(event, "data", event)),
            }
        )

    def save_group_messages(self, group_id: str, messages: list[Any]) -> int:
        """批量保存从群历史接口拉取到的消息。

        Args:
            group_id: 消息所属群号。
            messages: 历史消息对象列表。

        Returns:
            成功写入或更新的消息数量。
        """

        saved_count = 0
        for message in messages:
            if self._save_group_message_from_history(group_id, message):
                saved_count += 1
        return saved_count

    def save_private_messages(self, peer_user_id: str, messages: list[Any]) -> int:
        """批量保存从私聊历史接口拉取到的消息。

        Args:
            peer_user_id: 私聊会话中的对方 QQ 号。
            messages: 历史消息对象列表。

        Returns:
            成功写入或更新的消息数量。
        """

        saved_count = 0
        for message in messages:
            if self._save_private_message_from_history(peer_user_id, message):
                saved_count += 1
        return saved_count

    def count_group_messages(
        self,
        group_id: str,
        start_timestamp: int,
        end_timestamp: int,
    ) -> int:
        """统计指定群在时间范围内的消息总数。"""

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM group_messages
                WHERE group_id = ?
                  AND time BETWEEN ? AND ?
                """,
                (str(group_id), int(start_timestamp), int(end_timestamp)),
            ).fetchone()
        return int(row[0] if row else 0)

    def get_group_message_rank(
        self,
        group_id: str,
        start_timestamp: int,
        end_timestamp: int,
        limit: int | None = None,
    ) -> dict[str, int]:
        """查询指定群在时间范围内的发言次数排行。

        Args:
            group_id: 群号。
            start_timestamp: 统计起始时间戳。
            end_timestamp: 统计结束时间戳。
            limit: 最多返回多少名；为空时返回完整排行。

        Returns:
            按发言次数降序排列的字典，键为用户 QQ 号，值为发言次数。
        """

        sql = """
            SELECT user_id, COUNT(*) AS message_count
            FROM group_messages
            WHERE group_id = ?
              AND time BETWEEN ? AND ?
              AND user_id <> ''
            GROUP BY user_id
            ORDER BY message_count DESC, user_id ASC
        """
        params: list[Any] = [str(group_id), int(start_timestamp), int(end_timestamp)]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return {str(row["user_id"]): int(row["message_count"]) for row in rows}

    def get_group_display_name(self, group_id: str, user_id: str) -> str | None:
        """从已入库消息中获取用户最近一次可用的群内展示名。"""

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT sender_card, sender_nickname
                FROM group_messages
                WHERE group_id = ?
                  AND user_id = ?
                  AND (
                      (sender_card IS NOT NULL AND sender_card <> '')
                      OR (sender_nickname IS NOT NULL AND sender_nickname <> '')
                  )
                ORDER BY time DESC
                LIMIT 1
                """,
                (str(group_id), str(user_id)),
            ).fetchone()

        if row is None:
            return None
        return row["sender_card"] or row["sender_nickname"] or None

    def _save_group_message_from_history(self, group_id: str, message: Any) -> bool:
        """保存一条群历史消息对象。"""

        return self._save_group_record(
            {
                "group_id": str(group_id),
                "message_id": self._text(self._field(message, "message_id")),
                "real_id": self._text(self._field(message, "real_id")),
                "message_type": self._text(self._field(message, "message_type")),
                "time": self._int(self._field(message, "time")),
                "user_id": self._message_user_id(message),
                "sender_nickname": self._sender_text(message, "nickname"),
                "sender_card": self._sender_text(message, "card"),
                "sender_role": self._sender_text(message, "role"),
                "raw_message": self._text(self._field(message, "raw_message")),
                "message_segments_json": self._message_segments_json(message),
                "message_json": self._object_json(message),
            }
        )

    def _save_private_message_from_history(
        self,
        peer_user_id: str,
        message: Any,
    ) -> bool:
        """保存一条私聊历史消息对象。"""

        return self._save_private_record(
            {
                "peer_user_id": str(peer_user_id),
                "message_id": self._text(self._field(message, "message_id")),
                "real_id": self._text(self._field(message, "real_id")),
                "message_type": self._text(self._field(message, "message_type")),
                "time": self._int(self._field(message, "time")),
                "sender_user_id": self._message_user_id(message),
                "sender_nickname": self._sender_text(message, "nickname"),
                "raw_message": self._text(self._field(message, "raw_message")),
                "message_segments_json": self._message_segments_json(message),
                "message_json": self._object_json(message),
            }
        )

    def _save_group_record(self, record: dict[str, Any]) -> bool:
        """写入或更新一条群消息记录。"""

        if not record["group_id"] or not record["message_id"]:
            return False

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO group_messages (
                    group_id,
                    message_id,
                    real_id,
                    message_type,
                    time,
                    user_id,
                    sender_nickname,
                    sender_card,
                    sender_role,
                    raw_message,
                    message_segments_json,
                    message_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(group_id, message_id) DO UPDATE SET
                    real_id = COALESCE(NULLIF(excluded.real_id, ''), group_messages.real_id),
                    message_type = COALESCE(NULLIF(excluded.message_type, ''), group_messages.message_type),
                    time = CASE
                        WHEN excluded.time > 0 THEN excluded.time
                        ELSE group_messages.time
                    END,
                    user_id = COALESCE(NULLIF(excluded.user_id, ''), group_messages.user_id),
                    sender_nickname = COALESCE(NULLIF(excluded.sender_nickname, ''), group_messages.sender_nickname),
                    sender_card = COALESCE(NULLIF(excluded.sender_card, ''), group_messages.sender_card),
                    sender_role = COALESCE(NULLIF(excluded.sender_role, ''), group_messages.sender_role),
                    raw_message = CASE
                        WHEN excluded.raw_message IS NOT NULL AND excluded.raw_message <> ''
                        THEN excluded.raw_message
                        ELSE group_messages.raw_message
                    END,
                    message_segments_json = CASE
                        WHEN excluded.message_segments_json IS NOT NULL
                             AND excluded.message_segments_json <> ''
                             AND excluded.message_segments_json <> '[]'
                        THEN excluded.message_segments_json
                        ELSE group_messages.message_segments_json
                    END,
                    message_json = CASE
                        WHEN (excluded.raw_message IS NOT NULL AND excluded.raw_message <> '')
                             OR (
                                excluded.message_segments_json IS NOT NULL
                                AND excluded.message_segments_json <> ''
                                AND excluded.message_segments_json <> '[]'
                             )
                        THEN excluded.message_json
                        ELSE group_messages.message_json
                    END
                """,
                (
                    record["group_id"],
                    record["message_id"],
                    record["real_id"],
                    record["message_type"],
                    record["time"],
                    record["user_id"],
                    record["sender_nickname"],
                    record["sender_card"],
                    record["sender_role"],
                    record["raw_message"],
                    record["message_segments_json"],
                    record["message_json"],
                ),
            )
        return True

    def _save_private_record(self, record: dict[str, Any]) -> bool:
        """写入或更新一条私聊消息记录。"""

        if not record["peer_user_id"] or not record["message_id"]:
            return False

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO private_messages (
                    peer_user_id,
                    message_id,
                    real_id,
                    message_type,
                    time,
                    sender_user_id,
                    sender_nickname,
                    raw_message,
                    message_segments_json,
                    message_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(peer_user_id, message_id) DO UPDATE SET
                    real_id = COALESCE(NULLIF(excluded.real_id, ''), private_messages.real_id),
                    message_type = COALESCE(NULLIF(excluded.message_type, ''), private_messages.message_type),
                    time = CASE
                        WHEN excluded.time > 0 THEN excluded.time
                        ELSE private_messages.time
                    END,
                    sender_user_id = COALESCE(NULLIF(excluded.sender_user_id, ''), private_messages.sender_user_id),
                    sender_nickname = COALESCE(NULLIF(excluded.sender_nickname, ''), private_messages.sender_nickname),
                    raw_message = CASE
                        WHEN excluded.raw_message IS NOT NULL AND excluded.raw_message <> ''
                        THEN excluded.raw_message
                        ELSE private_messages.raw_message
                    END,
                    message_segments_json = CASE
                        WHEN excluded.message_segments_json IS NOT NULL
                             AND excluded.message_segments_json <> ''
                             AND excluded.message_segments_json <> '[]'
                        THEN excluded.message_segments_json
                        ELSE private_messages.message_segments_json
                    END,
                    message_json = CASE
                        WHEN (excluded.raw_message IS NOT NULL AND excluded.raw_message <> '')
                             OR (
                                excluded.message_segments_json IS NOT NULL
                                AND excluded.message_segments_json <> ''
                                AND excluded.message_segments_json <> '[]'
                             )
                        THEN excluded.message_json
                        ELSE private_messages.message_json
                    END
                """,
                (
                    record["peer_user_id"],
                    record["message_id"],
                    record["real_id"],
                    record["message_type"],
                    record["time"],
                    record["sender_user_id"],
                    record["sender_nickname"],
                    record["raw_message"],
                    record["message_segments_json"],
                    record["message_json"],
                ),
            )
        return True

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """创建 SQLite 连接，并在使用结束后关闭连接。"""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            conn.close()

    @classmethod
    def _message_user_id(cls, message: Any) -> str:
        """从消息对象或发送者对象中提取发送者 QQ 号。"""

        sender = cls._field(message, "sender")
        user_id = cls._field(message, "user_id") or cls._field(sender, "user_id")
        return cls._text(user_id)

    @classmethod
    def _sender_text(cls, message: Any, field_name: str) -> str:
        """从消息发送者对象中提取指定文本字段。"""

        sender = cls._field(message, "sender")
        return cls._text(cls._field(sender, field_name))

    @classmethod
    def _message_segments_json(cls, message: Any) -> str | None:
        """把消息段列表序列化为 JSON 字符串。"""

        segments = cls._field(message, "message")
        if segments is None:
            return None
        return cls._json_dumps(cls._jsonable(segments))

    @classmethod
    def _object_json(cls, value: Any) -> str:
        """把完整消息对象序列化为 JSON 字符串。"""

        return cls._json_dumps(cls._jsonable(value))

    @classmethod
    def _json_dumps(cls, value: Any) -> str:
        """以 UTF-8 友好的形式生成 JSON 字符串。"""

        return json.dumps(value, ensure_ascii=False, default=str)

    @classmethod
    def _jsonable(cls, value: Any) -> Any:
        """把 Pydantic、消息段和枚举等对象转成可 JSON 序列化的数据。"""

        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if hasattr(value, "model_dump"):
            try:
                return value.model_dump(mode="json")
            except TypeError:
                return value.model_dump()

        if hasattr(value, "to_list"):
            return cls._jsonable(value.to_list())

        if hasattr(value, "to_dict"):
            return cls._jsonable(value.to_dict())

        if hasattr(value, "value"):
            return cls._jsonable(value.value)

        if isinstance(value, dict):
            return {str(key): cls._jsonable(item) for key, item in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [cls._jsonable(item) for item in value]

        return str(value)

    @staticmethod
    def _field(value: Any, field_name: str, default: Any = None) -> Any:
        """兼容对象属性和字典键读取字段。"""

        if value is None:
            return default
        if isinstance(value, dict):
            return value.get(field_name, default)
        return getattr(value, field_name, default)

    @classmethod
    def _text(cls, value: Any) -> str:
        """把字段值规范化为字符串，空值返回空字符串。"""

        if value is None:
            return ""
        if hasattr(value, "value"):
            value = value.value
        return str(value)

    @staticmethod
    def _int(value: Any) -> int:
        """把字段值规范化为整数，无法转换时返回 0。"""

        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
