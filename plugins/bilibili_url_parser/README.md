# BilibiliUrlParser - B站视频链接解析插件

[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](https://github.com/GEYUANwuqi/ncatbot.plugin.BilibiliUrlParser)
[![Author](https://img.shields.io/badge/author-物起-green.svg)](https://github.com/GEYUANwuqi)
[![NcatBot](https://img.shields.io/badge/NcatBot-github-orange.svg)](https://github.com/liyihao1110/ncatbot)
[![Forum](https://img.shields.io/badge/NcatBot-论坛-red.svg)](https://www.ityzs.com/)
[![访问量统计](https://visitor-badge.laobi.icu/badge?page_id=GEYUANwuqi.ncatbot.plugin.BilibiliUrlParser)](https://github.com/GEYUANwuqi/ncatbot.plugin.BilibiliUrlParser)


一个用于 NcatBot 的 B 站视频链接解析插件，支持自动识别并解析群聊中的 B 站视频链接，获取视频详细信息。

## 📋 功能特性

- ✅ **多格式支持**：支持 BV 号、AV 号、完整链接、短链接、小程序等多种格式
- ✅ **自动识别**：自动监听消息中的 B 站链接，无需手动触发
- ✅ **基础信息**：获取视频标题、UP 主、BV 号、av 号和快捷链接
- ✅ **短链重定向**：自动处理 b23.tv 短链接并解析真实视频地址
- ✅ **小程序解析**：支持解析 QQ 分享的 B 站小程序消息
- ✅ **群聊私聊**：同时支持群组消息和私聊消息
- ✅ **异步处理**：采用异步机制，高效稳定

## 📦 安装

### 依赖项

确保已安装以下 Python 库：

```bash
pip install bilibili-api-python
pip install aiohttp
```

### 安装插件

1. 确保已安装 NcatBot
2. 将本插件放置到 NcatBot 的插件目录 `./plugins` 中
3. 重启 NcatBot 或重载插件

```bash
# 克隆插件到插件目录
cd /path/to/ncatbot/plugins
git clone https://github.com/GEYUANwuqi/ncatbot.plugin.BilibiliUrlParser.git
```

## ⚙️ 配置

插件默认无需额外配置即可使用。如需使用需要登录才能访问的功能，可以配置 `sessdata`。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `sessdata` | `str` | `""` | B 站登录凭证（可选） |

配置文件会自动保存在 NcatBot 的配置目录中。

注：暂未开放

## 🚀 使用方法

安装完成后，插件会自动监听所有消息。当检测到消息中包含 B 站视频链接时，会自动解析并回复视频信息。

### 支持的链接格式

| 格式类型 | 示例 | 说明 |
|---------|------|------|
| BV 号 | `BV1xx411c7mD` | 直接发送 BV 号 |
| AV 号 | `av170001` | 直接发送 AV 号 |
| 完整链接 | `https://www.bilibili.com/video/BV1xx411c7mD` | 标准视频链接 |
| 短链接 | `https://b23.tv/xxxxx` | B 站短链接 |
| 小程序 | （QQ分享消息） | QQ 中分享的 B 站小程序 |

### 使用示例

**示例 1：发送完整链接**
```
快来看这个视频！https://www.bilibili.com/video/BV1xx411c7mD
```

**示例 2：直接发送 BV 号**
```
BV1xx411c7mD
```

**示例 3：发送短链接**
```
https://b23.tv/xxxxx
```

**示例 4：分享小程序**
- 在 QQ 中直接分享 B 站视频小程序即可

### 回复格式示例

```
标题: 奔着疑难杂症去的，结果原因很简单。。。又是捡漏了。
UP主: 城阳电工电路 (UID: 1985127693)
BV号: BV1ZuqyByEGy
av号: av115754653457072
快捷链接: https://www.bilibili.com/video/BV1ZuqyByEGy
```

## 🔧 工作原理

### 链接解析流程

1. **消息监听**：监听所有群聊和私聊消息
2. **链接提取**：使用正则表达式匹配消息中的 B 站链接
3. **格式识别**：识别链接类型（BV 号、AV 号、短链接、小程序等）
4. **短链重定向**：如果是短链接，通过 HTTP HEAD 请求获取真实链接
5. **视频信息获取**：调用 bilibili-api 获取视频详细信息
6. **信息格式化**：将视频基础信息格式化为易读的文本
7. **消息回复**：发送格式化后的信息

### 支持的链接格式正则

- **BV 号**：`[bB][vV][1-9A-HJ-NP-Za-km-z]{10}`
- **AV 号**：`[aA][vV](\d+)`

### 技术特点

- **异步处理**：使用 `aiohttp` 进行异步 HTTP 请求
- **超时控制**：短链接重定向设置 10 秒超时，避免长时间等待
- **错误处理**：完善的异常捕获和错误日志记录
- **智能截断**：简介内容超过 100 字符自动截断

### 代码结构

| 方法名 | 功能描述 |
|--------|---------|
| `get_bili_vid(url)` | 解析 B 站链接，返回 BV 号或 AV 号 |
| `get_b23_url(msg)` | 从消息中提取特殊格式的 b23.tv 链接 |
| `process_bili_url(msg)` | 统一处理 B 站链接入口 |
| `get_bv_info(video_id)` | 获取视频详细信息并格式化 |
| `group_message(msg)` | 消息处理入口（群聊和私聊） |

## ⚠️ 注意事项

1. **API 限制**：插件使用 `bilibili-api` 库，可能受到 B 站 API 访问限制
2. **网络超时**：短链接重定向设置了 10 秒超时，网络不稳定时可能解析失败
3. **详细字段**：播放数据、分区、发布时间、简介和封面图发送逻辑已在代码中注释保留
4. **无需权限**：插件对所有用户开放，无需管理员权限

## 🐛 故障排除

### 插件无法加载
- 检查 NcatBot 版本和 Napcat 版本是否兼容
- 确认依赖库 `bilibili-api` 和 `aiohttp` 已正确安装
- 检查插件路径是否正确

### 链接无法解析
- 确认链接格式是否正确
- 检查网络连接是否正常
- 查看日志中的错误信息
- 尝试访问 B 站官网确认视频是否存在

### 短链接解析失败
- 可能是网络超时，请重试
- 检查短链接是否已失效
- 查看日志中的详细错误信息

### 封面图片无法显示
- 确认图片链接是否可访问
- 检查 NcatBot 的图片发送功能是否正常
- 查看网络连接状态

## 👨‍💻 开发者

- **作者**：物起
- **描述**：解析bv号av号url链接b站小程序

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

如果你有任何改进建议或发现了 Bug，请随时：
- 提交 [Issue](https://github.com/GEYUANwuqi/ncatbot.plugin.BilibiliUrlParser/issues)
- 发起 [Pull Request](https://github.com/GEYUANwuqi/ncatbot.plugin.BilibiliUrlParser/pulls)

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/GEYUANwuqi/ncatbot.plugin.BilibiliUrlParser/issues)
- 发送邮件至：yzd627350525@gmail.com

## 🔗 相关链接

- [NcatBot 官方仓库](https://github.com/liyihao1110/ncatbot)
- [NcatBot 论坛](https://www.ityzs.com/)
- [bilibili-api 文档](https://github.com/Nemo2011/bilibili-api)

---

**⭐ 如果这个插件对你有帮助，请给个 Star 支持一下！**
