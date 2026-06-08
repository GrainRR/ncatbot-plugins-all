
import os

from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent


FORBIDDEN_WORDS_FILE = os.path.join(
    os.path.dirname(__file__),
    "forbidden_words.txt",
)


class SetGroupForbiddenWord(NcatBotPlugin):

    async def on_load(self):
        """插件加载时输出加载日志。"""

        self.logger.info(f"{self.name} 违禁词已加载")

    @registrar.qq.on_group_message()
    async def check_forbidden_word(self, event: GroupMessageEvent):
        """检查群消息中是否包含违禁词。

        Args:
            event: 触发检查的群消息事件。
        """

        # 提取所有纯文本消息段，并拼接成待检测的完整文本。
        message_text = ""
        for segment in event.message.filter_text():
            message_text += segment.text

        words = _read_forbidden_words()

        for word in words:
            if word in message_text:
                await event.reply(f"检测到违禁词：{word}")
                await self.api.qq.messaging.delete_msg(event.message_id)
            
    @registrar.qq.on_group_command("#添加违禁词", ignore_case=True)
    async def add_group_forbidden_word(
            self,
            event: GroupMessageEvent,
            word: str | None = None
    ):
        """添加一个新的违禁词。

        Args:
            event: 触发命令的消息事件。
            word: 需要添加的违禁词。为空时提示用户补充内容。
        """

        if not word:
            await event.reply("请使用类似：#添加违禁词 目标违禁词 的格式来添加违禁词")
            return

        word = word.strip()
        words = _read_forbidden_words()

        if word in words:
            await event.reply("违禁词已存在")
            return

        with open(FORBIDDEN_WORDS_FILE, "a", encoding="utf-8") as f:
            f.write(word + "\n")

        await event.reply("违禁词添加成功")

    @registrar.qq.on_group_command("#删除违禁词", ignore_case=True)
    async def delete_group_forbidden_word(
            self,
            event: GroupMessageEvent,
            word: str | None = None
    ):
        """删除一个已有的违禁词。

        Args:
            event: 触发命令的消息事件。
            word: 需要删除的违禁词。为空时提示用户补充内容。
        """

        if not word:
            await event.reply("请使用类似：#删除违禁词 目标违禁词 的格式来删除违禁词")
            return

        word = word.strip()
        words = _read_forbidden_words()

        if word not in words:
            await event.reply("违禁词不存在")
            return

        words.remove(word)
        _write_forbidden_words(words)
        await event.reply("违禁词删除成功")

    @registrar.qq.on_group_command("#违禁词列表", ignore_case=True)
    async def list_group_forbidden_words(self, event: GroupMessageEvent):
        """查看当前已配置的违禁词列表。

        Args:
            event: 触发命令的消息事件。
        """

        words = _read_forbidden_words()

        if not words:
            await event.reply("当前没有配置违禁词")
            return

        message = "当前违禁词列表：\n" + "\n".join(words)
        await event.reply(message)


def _write_forbidden_words(words: list[str]):
    """将违禁词列表写回文件。

    Args:
        words: 需要保存的违禁词列表。
    """

    with open(FORBIDDEN_WORDS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(words))
        if words:
            f.write("\n")


def _read_forbidden_words() -> list[str]:
    """从文件中读取违禁词列表。

    Returns:
        去除空行和首尾空白后的违禁词列表。
    """

    try:
        with open(FORBIDDEN_WORDS_FILE, "r", encoding="utf-8-sig") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []
