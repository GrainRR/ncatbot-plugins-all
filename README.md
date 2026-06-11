# TinglanBot 插件说明

本文仅说明当前仓库内各插件的基本功能和安装方式。

## 插件功能

### group_special_title

群成员专属头衔插件。

- 群成员可以申请自己的专属头衔。
- 群主或管理员可以为群成员发放专属头衔。
- 头衔长度限制为最多 6 个汉字或 12 个半角字符。

### group_daily_report

群聊每日报表插件。

- 自动保存群聊消息记录。
- 支持生成今日、昨日或指定日期的群发言排行。
- 报表包含当日消息总数和发言前 10 名。

### group_forbidden_words

群违禁词管理插件。

- 检测群消息中的违禁词。
- 命中违禁词后提示并撤回消息。
- 支持添加、删除和查看违禁词。

### bilibili_url_parser

B 站视频链接解析插件。

- 自动识别群聊或私聊中的 B 站视频链接。
- 支持 BV 号、AV 号、完整链接、短链接和 QQ 分享小程序。
- 回复视频标题、UP 主、播放数据、简介和封面等信息。

## 安装方式

将 `/path/to/your/ncatbot` 替换为你的 NcatBot 项目目录。

### 安装 group_special_title

```bash
cd /path/to/your/ncatbot/plugins
git clone https://github.com/GrainRR/ncatbot-plugin-set-group-special-title.git group_special_title
```

### 安装 group_daily_report

```bash
cd /path/to/your/ncatbot/plugins
git clone https://github.com/GrainRR/ncatbot-plugin-generate-daily-report.git group_daily_report
```

### 安装 group_forbidden_words

```bash
cd /path/to/your/ncatbot/plugins
git clone https://github.com/GrainRR/ncatbot-plugin-set-group-forbidden-word.git group_forbidden_words
```

### 安装 bilibili_url_parser

```bash
cd /path/to/your/ncatbot/plugins
git clone https://github.com/GrainRR/ncatbot-plugin-bilibili-url-parser.git bilibili_url_parser
pip install bilibili-api-python aiohttp
```

安装完成后，重启机器人即可加载插件。
