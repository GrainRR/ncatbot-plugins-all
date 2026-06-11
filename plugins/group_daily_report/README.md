# group_daily_report

群聊每日报表插件。

## 重要：必须先安装 message_archive

`group_daily_report` 依赖 `message_archive` 提供的消息数据库。

未安装或未启用 `message_archive` 时，本插件无法获得聊天记录，也就无法生成有效报表。

```bash
cd /path/to/your/ncatbot/plugins
git clone https://github.com/GrainRR/ncatbot-plugin-message-archive.git message_archive
```

## 功能

- 基于 `message_archive` 的消息数据库生成报表
- 生成指定日期的群发言排行
- 显示当日消息总数和前 10 名

## 依赖

- 必须先安装并启用 `message_archive` 插件。

## 命令

```text
#每日报表
#每日报表 今日
#每日报表 昨日
#每日报表 YYYY-MM-DD
```

## 权限

- 群成员均可使用。

## 数据文件

```text
data/message_archive/messages.sqlite
```
