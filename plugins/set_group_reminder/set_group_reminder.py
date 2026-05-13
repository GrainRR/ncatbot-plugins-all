import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin


class SetGroupReminderPlugin(NcatBotPlugin):
    name = "set_group_reminder"
    version = "0.1.0"
    author = "Li"
    description = "设置群提醒任务"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reminders_file = Path(__file__).parent / "reminders.json"
        self.reminders: Dict[int, List[Dict]] = self._load_reminders()

    def _load_reminders(self) -> Dict[int, List[Dict]]:
        """从文件加载提醒数据"""
        if self.reminders_file.exists():
            try:
                with open(self.reminders_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载提醒数据失败: {e}")
        return {}

    def _save_reminders(self):
        """保存提醒数据到文件"""
        try:
            with open(self.reminders_file, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存提醒数据失败: {e}")

    @registrar.qq.on_group_command("#设置提醒")
    async def set_reminder(
        self, event: GroupMessageEvent, remind_time: str = "", content: str = ""
    ):
        """设置群提醒
        
        用法: #设置提醒 HH:MM 提醒内容
        例: #设置提醒 10:30 站会时间到了
        """
        if not remind_time or not content:
            await event.reply(
                "用法: #设置提醒 HH:MM 提醒内容\n"
                "例: #设置提醒 10:30 站会时间到了喵"
            )
            return

        try:
            # 验证时间格式
            datetime.strptime(remind_time, "%H:%M")
        except ValueError:
            await event.reply("时间格式错误，请使用 HH:MM 格式（如 10:30）喵")
            return

        group_id = event.group_id
        if group_id not in self.reminders:
            self.reminders[group_id] = []

        # 检查是否已存在相同的提醒时间
        for reminder in self.reminders[group_id]:
            if reminder["time"] == remind_time:
                await event.reply(f"提醒时间 {remind_time} 已经存在了喵，请更改时间~")
                return

        reminder_data = {
            "time": remind_time,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "created_by": event.user_id,
        }

        self.reminders[group_id].append(reminder_data)
        self._save_reminders()

        await event.reply(
            f"✅ 已添加提醒\n时间: {remind_time}\n内容: {content}\n喵~"
        )

    @registrar.qq.on_group_command("#删除提醒")
    async def remove_reminder(self, event: GroupMessageEvent, remind_time: str = ""):
        """删除群提醒
        
        用法: #删除提醒 HH:MM
        例: #删除提醒 10:30
        """
        if not remind_time:
            await event.reply("用法: #删除提醒 HH:MM\n例: #删除提醒 10:30喵")
            return

        group_id = event.group_id
        if group_id not in self.reminders or not self.reminders[group_id]:
            await event.reply("该群组没有设置任何提醒喵")
            return

        # 查找并删除提醒
        found = False
        for i, reminder in enumerate(self.reminders[group_id]):
            if reminder["time"] == remind_time:
                removed = self.reminders[group_id].pop(i)
                self._save_reminders()
                await event.reply(
                    f"✅ 已删除提醒\n时间: {remind_time}\n内容: {removed['content']}喵"
                )
                found = True
                break

        if not found:
            await event.reply(f"未找到时间为 {remind_time} 的提醒喵")

    @registrar.qq.on_group_command("#查看提醒")
    async def list_reminders(self, event: GroupMessageEvent):
        """查看群提醒列表"""
        group_id = event.group_id
        
        if group_id not in self.reminders or not self.reminders[group_id]:
            await event.reply("该群组没有设置任何提醒喵")
            return

        reminders_list = self.reminders[group_id]
        message = "📋 该群组的提醒列表:\n\n"

        for idx, reminder in enumerate(reminders_list, 1):
            message += (
                f"{idx}. 时间: {reminder['time']}\n"
                f"   内容: {reminder['content']}\n"
                f"   创建者: {reminder['created_by']}\n\n"
            )

        await event.reply(message)

    @registrar.qq.on_group_command("#清空提醒")
    async def clear_reminders(self, event: GroupMessageEvent):
        """清空群提醒列表"""
        group_id = event.group_id
        
        if group_id not in self.reminders or not self.reminders[group_id]:
            await event.reply("该群组没有任何提醒可清空喵")
            return

        count = len(self.reminders[group_id])
        self.reminders[group_id] = []
        self._save_reminders()

        await event.reply(f"✅ 已清空 {count} 条提醒喵")
