# ⚠️ 重要通知

<div align="center">
  
**本项目正在进行完全重构，目前仅保持最低限度维护**

我正在努力开发全新版本，以提供更好的性能和用户体验。
在重构完成前，当前版本将只进行关键问题修复。
感谢您的理解与支持！

</div>

---

# 🌟 SpectreCore (影芯) - 智能群聊互动插件

<div align="center">

![SpectreCore](https://avatars.githubusercontent.com/u/129108081?s=48&v=4)

[![version](https://img.shields.io/badge/version-v1.0.4-blue.svg?style=flat-square)](https://github.com/23q3/astrbot_plugin_SpectreCore)
[![license](https://img.shields.io/badge/license-AGPL--3.0-green.svg?style=flat-square)](LICENSE)
[![author](https://img.shields.io/badge/author-23q3-orange.svg?style=flat-square)](https://github.com/23q3)

*让 AI 成为群聊中最受欢迎的成员*

</div>

<p align="center">
  <a href="#-简介">简介</a> •
  <a href="#-特性">特性</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-配置说明">配置说明</a> •
  <a href="#-指令说明">指令说明</a> •
  <a href="#-使用技巧">使用技巧</a> •
  <a href="#-更新日志">更新日志</a>
</p>

---

## 📝 简介

<table>
<tr>
<td>

SpectreCore (影芯) 是一个为 AstrBot 设计的高级群聊互动插件，它能让大语言模型更好地参与到群聊对话中，带来生动和沉浸式的群聊体验。通过智能的消息处理和上下文理解，让 AI 像真实群友一样自然地参与讨论。

> 💡 **灵感来源**：本项目的灵感来自 [【当你发现聊了99+的群友是DeepSeek.......】](https://www.bilibili.com/video/BV1amAneGE3P)

</td>
</tr>
</table>

## ✨ 特性

- 🤖 **智能消息识别与回复** - 自动分析群聊上下文进行回复
- 🎭 **支持自定义 AI 人格设定** - 让 AI 拥有特定的性格与说话风格
- 📸 **支持图片理解和多模态互动** - 可以理解并回复包含图片的消息
- 📜 **群聊历史记录保存与上下文理解** - 记住之前的对话内容，保持连贯性
- ⚡ **高性能消息处理** - 高效处理大量群消息并控制历史记录大小
- 🔧 **灵活的配置选项** - 可根据需求自定义插件行为
- 🔍 **支持读空气** - AI 可智能判断何时应该回复，何时保持沉默
- 🔒 **并发控制** - 防止同一群组多次并发调用大模型
- 📨 **高级消息格式处理**
  - ✓ 支持合并转发消息解析
  - ✓ 支持 @ 消息智能理解
  - ✓ 支持引用消息上下文关联
  - ✓ 自动将复杂消息转换为大模型可理解的格式

## 🚀 快速开始

### 安装

<details>
<summary>展开查看安装步骤</summary>

1. 首先确保已部署 [AstrBot](https://github.com/Soulter/AstrBot)
2. 在插件市场中搜索 SpectreCore 点击安装
   或点击右下角加号，输入本插件仓库链接安装：
   ```
   https://github.com/23q3/astrbot_plugin_SpectreCore
   ```
3. 打开插件的配置界面，配置好相关选项，即可开始使用

</details>

## ⚙️ 配置说明

插件支持多种配置选项，可以在 AstrBot 的插件管理界面进行设置：

<div align="center">

| 配置项 | 说明 | 默认值 |
|:------|:-----|:-------|
| `group_msg_history` | 输入给大模型的消息数量上限 | 100 |
| `image_count` | 输入给大模型的图片数量上限 | 0 |
| `enabled_groups` | 启用回复功能的群聊列表 | [] |
| `filter_thinking` | 过滤大模型回复中被标签包裹的思考内容 | 开启 |
| `persona` | 使用的人格名称 | 空 |
| `read_air` | 是否开启读空气功能 | 关闭 |
| `use_func_tool` | 是否启用函数工具 | 关闭 |
| `model_frequency` | 决定调用模型回复的频率 | - |

</div>

### 模型频率配置

`model_frequency` 配置包含以下选项：

- **keywords**: 关键词触发列表，消息包含这些关键词时必定触发回复
- **method**: 回复方式，目前支持"概率回复"
- **probability**: 在没有关键词触发的情况下，回复的概率(0-1之间的小数)

## 📖 指令说明

SpectreCore插件支持以下指令，所有指令均可使用 `/spectrecore` 或简写 `/sc` 作为前缀：

<div align="center">

| 指令 | 说明 | 用法示例 |
|:-----|:-----|:--------|
| help<br>帮助 | 查看插件帮助信息 | `/sc help`<br>`/sc 帮助` |
| reset | 重置群聊记录 | 在群聊中：`/sc reset`<br>在私聊中：`/sc reset 123456789` |

</div>

### 指令详解

<details>
<summary><b>帮助指令 (help/帮助)</b></summary>

显示插件的基本帮助信息，包括可用命令和简要使用说明。

**用法**：
- `/sc help` - 查看帮助信息
- `/sc 帮助` - 同上，中文别名

**响应**：
插件会返回包含可用命令和使用方法的帮助文本。
</details>

<details>
<summary><b>重置群聊记录 (reset)</b></summary>

重置指定群聊的历史消息记录，清空该群的聊天上下文。

**用法**：
- 在群聊中：`/sc reset` - 重置当前群的聊天记录
- 在私聊中：`/sc reset 群号` - 重置指定群的聊天记录，如 `/sc reset 123456789`

**参数**：
- 群号 (可选) - 要重置记录的群聊号码，如果在群聊中使用可省略（默认使用当前群）

**响应**：
- 成功：`已重置群 xxx 的聊天记录`
- 无记录：`群 xxx 没有聊天记录文件，可能已经被重置`
- 参数错误：`请提供有效的群号` 或 `请提供要重置聊天记录的群号，例如：/sc reset 123456789`

**说明**：
此命令将删除指定群聊的历史消息文件，使大模型"忘记"之前的对话内容。在需要清除敏感信息或重新开始对话时非常有用。
</details>

## 💡 使用技巧

### 如何让 AI 读空气？

<details>
<summary>展开查看详细设置</summary>

1. 在插件配置中开启 `read_air` 功能
2. 在人格设置中添加提示，例如：
   ```
   当群聊中出现以下情况时，请不要回复：
   1. 群友在讨论专业话题，而你无法提供有价值的见解
   2. 群内正在进行命令操作，不需要你的干扰
   3. 当话题与你无关，或者你的回复可能会打断当前的对话流
   ```
3. AI 会根据你设置的提示自动判断何时应该回复，何时保持沉默

> **注意**：已知deepseek-v3模型在不配置提示词的情况下会频繁沉默，请配置好提示词以获得理想效果。
</details>

## 🔧 支持的消息适配器

<div align="center">
  
| 平台 | 状态 | 说明 |
|:-----|:----:|:-----|
| aiocqhttp | ✅ | 完全支持 |
| 其他平台 | ❌ | 暂不支持，欢迎贡献适配器 |

</div>

## 📋 更新日志

<details open>
<summary><b>最新版本</b></summary>

### v1.0.4 (2025-03-12)
- 🐛 修正处理大模型回复时的条件判断逻辑[issue#15](https://github.com/23q3/astrbot_plugin_SpectreCore/issues/15)

</details>

<details>
<summary><b>历史版本</b></summary>

### v1.0.3 (2025-03-11)
- 🐛 在处理大模型回复时增加了对角色的判断，避免调用函数工具时出错[issue#15](https://github.com/23q3/astrbot_plugin_SpectreCore/issues/15)
- 🐛 在提示词增加了bot的昵称和qq号，避免大模型不知道聊天记录中哪个是自己[issue#14](https://github.com/23q3/astrbot_plugin_SpectreCore/issues/14)

### v1.0.2 (2025-03-08)
- 🔒 添加了群组锁机制，防止并发调用大模型
- 🛠️ 优化了消息处理存储流程，极大提高了性能
- 🔍 添加了清除聊天记录的指令
- 🔍 添加了检测指令关键词不回复功能
- 📝 改进了代码结构

### v1.0.1 (2025-03-05)
- 🔍 增加了读空气功能
- 🔍 增加了函数工具开关配置
- 🔄 更换了request_llm方法调用大模型，提高兼容性
- 🛠️ 优化部分代码

### v1.0.0 (2025-03-04)
- 🎉 首次发布
- ✨ 实现基本的群聊互动功能

</details>

## ⚠️ 注意事项

- 代码部分由 AI 辅助生成，使用时请仔细甄别
- 本插件和 AstrBot 自带的主动回复功能之间没有任何联系，在使用本插件时请关闭 AstrBot 的主动回复功能，以免重复回复
- 为避免不必要的响应，建议开启读空气功能并为 AI 提示明确的回复条件

## 🔗 可能感兴趣的项目

<div align="center">
<table>
<tr>
<td align="center">
<a href="https://github.com/SengokuCola/MaiMBot">
<img src="https://avatars.githubusercontent.com/u/25811392?s=48&v=4" width="80" alt="MaiMBot"><br>
<sub><b>MaiMBot (麦麦)</b></sub>
</a><br>
<sub>一款专注于群组聊天的赛博网友QQ机器人</sub>
</td>
</tr>
</table>
</div>

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目！

<details>
<summary>贡献者</summary>

- [23q3](https://github.com/23q3) - 主要开发者
- 感谢所有提供反馈和建议的用户！

</details>

## 📄 许可证

<details>
<summary>查看许可证信息</summary>

本项目采用 GNU Affero General Public License v3.0 (AGPL-3.0) 许可证。这意味着：

- ✅ 您可以自由使用、修改和分发本软件
- ✅ 如果您修改了本软件，必须开源您的修改
- ✅ 如果您通过网络提供本软件的服务，必须开源您的完整源代码
- ✅ 任何衍生作品必须使用相同的许可证（AGPL-3.0）

详细信息请查看 [LICENSE](LICENSE) 文件。

</details>

---

<div align="center">

**[SpectreCore (影芯)](https://github.com/23q3/astrbot_plugin_SpectreCore)** | Powered by [AstrBot](https://github.com/Soulter/AstrBot)

<sub>Made with ❤️ by [23q3](https://github.com/23q3)</sub>

</div>
