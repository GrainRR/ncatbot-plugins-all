from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import At


def _get_halfwidth_units(text: str) -> int:
    """过滤超过 6 个汉字或 12 个英文/数字/半角字符的昵称"""
    units = 0

    for char in text:
        units += 1 if ord(char) < 128 else 2

    return units


class LiPluginPlugin(NcatBotPlugin):
    name = "set_group_special_title"
    version = "0.1.0"
    author = "Li"
    description = "设置群成员专属头衔"


    @registrar.qq.on_group_command("#申请头衔")
    async def set_title(self, event: GroupMessageEvent, title: str = ""):

        if not title:
            await event.reply("请填写头衔喵")
            return

        if _get_halfwidth_units(title) > 12:
            await event.reply("头衔过长了喵，最多只能设置 6 个汉字或 12 个英文/数字/半角字符喵")
            return

        try:
            #这里的set_group_special_title和文件名的set_group_special_title不是一码事
            #此处调用的是api.qq.manage的方法
            await self.api.qq.manage.set_group_special_title(
                event.group_id, event.user_id, special_title=title
            )
            await event.reply(f"✅ 已为 {event.user_id} 设置头衔「{title}」了喵~")
        except Exception as e:
            await event.reply(f"❌ 为 {event.user_id} 设置头衔「{title}」失败了喵QWQ")


    @registrar.qq.on_group_command("#发放头衔")
    async def set_title(self, event: GroupMessageEvent, target: At = None, title: str = ""):

        # 验证是否为群主或者管理
        if event.sender.role not in ("owner", "admin"):
            await event.reply("铸币喵")
            await self.api.qq.manage.set_group_special_title(
                event.group_id, event.sender.user_id, special_title="你是？"
            )
            return

        # 进行一个私货的夹带
        if target.user_id in ("2546589143", "3759015306"):
            await self.api.qq.manage.set_group_special_title(
                event.group_id, event.sender.user_id, special_title="忤逆圣上"
            )


        if target is None:
            await event.reply("请 @ 要设置头衔的人喵，不要手动复制或者直接输入文本信息要正确地 @ 出来喵")
            return
        if not title:
            await event.reply("请填写头衔喵")
            return

        try:
            await self.api.qq.manage.set_group_special_title(
                event.group_id, target.user_id, special_title=title
            )
            await event.reply(f"✅ 已为 {target.user_id} 设置头衔「{title}」了喵~")
        except Exception as e:
            await event.reply(f"❌ 为 {target.user_id} 设置头衔「{title}」失败了喵")


