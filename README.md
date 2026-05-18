# TinglanBot

TinglanBot 是一个基于 NcatBot 的 QQ 机器人项目，使用 NapCat 作为 QQ 连接端，通过插件目录加载机器人功能。

## 功能简介

- 连接 NapCat，接收并处理 QQ 群聊和私聊消息。
- 支持从 `plugins` 目录加载自定义插件。
- 内置示例插件：发送 `hello` 后回复 `hi`。
- 内置群头衔插件：支持群成员申请头衔，以及管理员为群成员发放头衔。

## 使用方式

分发版使用 `dist` 目录中的程序：

```text
dist\TinglanBot\TinglanBot.exe
```

使用时双击 `TinglanBot.exe` 启动。

注意：不要只单独复制 `TinglanBot.exe`。它需要和同目录下的 `_internal`、`plugins`、`data` 等目录一起使用。

分发版目录结构大致如下：

```text
TinglanBot\
  TinglanBot.exe
  _internal\
  plugins\
  data\
```

如果首次启动时没有 `config.yaml`，NcatBot 会按默认流程生成配置文件。按提示完成配置后再次启动即可。

## 插件说明

插件位于：

```text
plugins\
```

当前包含：

- `Li_plugin`：示例插件，收到 `hello` 指令后回复 `hi`。
- `set_group_special_title`：群头衔插件，用于申请或发放群成员专属头衔。

修改或新增插件后，重新启动程序即可加载最新内容。
