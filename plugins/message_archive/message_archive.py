from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin

from .message_store import MessageStore


class MessageArchive(NcatBotPlugin):
    """保存群聊和私聊消息到共享 SQLite 数据库。"""

    name = "message_archive"
    version = "0.1.0"
    description = "消息归档数据库"

    message_store: MessageStore

    async def on_load(self):
        """插件加载时创建或打开消息数据库。"""

        self.message_store = MessageStore(self.workspace / "messages.sqlite")
        self.message_store.init()
        self.logger.info("消息归档数据库已就绪: %s", self.message_store.db_path)

    @registrar.qq.on_group_message(priority=100)
    async def archive_group_message(self, event: GroupMessageEvent):
        """实时保存 Bot 收到的群消息。"""

        try:
            self.message_store.save_group_message_from_event(event)
        except Exception as exc:
            self.logger.exception("实时保存群消息失败: %s", exc)

    @registrar.qq.on_private_message(priority=100)
    async def archive_private_message(self, event: PrivateMessageEvent):
        """实时保存 Bot 收到的私聊消息。"""

        try:
            self.message_store.save_private_message_from_event(event)
        except Exception as exc:
            self.logger.exception("实时保存私聊消息失败: %s", exc)
