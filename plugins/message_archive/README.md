# message_archive

消息归档数据库插件。

## 安装方式

将 `/path/to/your/ncatbot` 替换为你的 NcatBot 项目目录。

```bash
cd /path/to/your/ncatbot/plugins
git clone https://github.com/GrainRR/ncatbot-plugin-message-archive.git message_archive
```

安装完成后，重启机器人即可加载插件。

## 功能

- 保存 Bot 实时收到的群聊消息。
- 保存 Bot 实时收到的私聊消息。
- 自动创建 `messages.sqlite` 数据库和所需数据表。
- 为其他插件提供消息统计和查询所需的共享数据库。

## 数据文件

```text
data/message_archive/messages.sqlite
```

如果该位置没有数据库，插件加载时会自动创建。
