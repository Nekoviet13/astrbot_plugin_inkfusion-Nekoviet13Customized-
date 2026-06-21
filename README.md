# 🎨 Inkfusion - AI 图片生成插件 for AstrBot

> 让机器人像真正的画家一样，主动提出画画并自动生成图片。

**本项目基于 [astrbot_plugin_inkfusion](https://github.com/fatsnk/astrbot_plugin_inkfusion) 修改**

> **⚠️ 许可证声明**: 本项目使用 **GNU Affero General Public License v3.0 (AGPL-3.0)** 授权。  
> 原始项目: [astrbot_plugin_inkfusion](https://github.com/fatsnk/astrbot_plugin_inkfusion) by F5  
> 修改作者: Nekoviet13  
> 修改日期: 2026-06-21

---

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 🎨 **AI 绘画** | 连接 Stable Diffusion WebUI API，根据文字描述生成图片 |
| 🧠 **智能识别** | 使用 LLM 判断是否为真正的画图意图，自动触发 |
| 📝 **提示词优化** | 自动将中文描述优化为英文提示词，提升生图质量 |
| 📁 **作品集管理** | 自动保存生成的图片，支持按关键词/日期检索 |
| 🤖 **LLM 工具调用** | AstrBot 的 LLM 可自动调用画图工具 |
| 🔌 **插件 API** | 提供 `draw()` 方法供其他插件调用 |
| 💬 **群聊/私聊** | 同时支持群聊和私聊环境 |

---

## 📦 安装

### 1. 安装插件

将插件放入 AstrBot 的 `data/plugins/` 目录：

```bash
cd AstrBot/data/plugins/
git clone https://github.com/Nekoviet13/astrbot_plugin_inkfusion.git
```

### 2. 安装依赖

```bash
pip install aiohttp
```

### 3. 配置 Stable Diffusion

确保 SD WebUI 已启动并添加 `--api` 参数：

```batch
set COMMANDLINE_ARGS=--api
```

### 4. 重启 AstrBot

---

## ⚙️ 配置

在 AstrBot WebUI 的「插件」页面，找到「AI图片生成插件」，点击「配置」。

### SD 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `sd_enabled` | 启用 SD 生图 | `false` |
| `sd_skip_ssl_verify` | 跳过 SSL 验证 | `false` |
| `sd_base_url` | SD WebUI API 地址 | `http://127.0.0.1:7860` |
| `sd_width` | 图片宽度 | `512` |
| `sd_height` | 图片高度 | `512` |
| `sd_positive_prompt` | 正面提示词模板 | `masterpiece, best quality, {{positive}}` |
| `sd_negative_prompt` | 负面提示词 | `bad quality, blurry...` |
| `sd_steps` | 采样步数 | `20` |
| `sd_cfg_scale` | 提示词引导系数 | `7.0` |
| `sd_sampler_name` | 采样器名称 | `Euler a` |
| `sd_scheduler` | 调度器（可选） | `空` |
| `sd_seed` | 随机种子 | `-1` |
| `sd_restore_faces` | 面部修复 | `false` |
| `sd_model_checkpoint` | 指定模型（可选） | `空` |
| `sd_clip_skip` | CLIP Skip（可选） | `0` |

### 提示词优化配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `enable_prompt_optimization` | 启用提示词优化 | `true` |
| `prompt_provider_name` | 使用的 Provider（留空使用默认） | `空` |
| `optimization_system_prompt` | 优化系统提示词 | 见配置模板 |

### 作品集配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `enable_local_save` | 启用本地保存 | `false` |
| `local_save_path` | 保存路径 | `./sd_images_gallery` |
| `save_with_prompt` | 保存提示词 | `true` |

---

## 🚀 使用方式

### 1. LLM 自动调用（推荐）

当用户发送包含"画图"、"画画"、"生成图片"等关键词的消息时，AstrBot 的 LLM 会自动调用 `draw_picture` 工具：

**用户**: "帮我画一只在星空下的猫"  
**机器人**: 调用工具 → 生成图片 → 发送图片

### 2. 自动触发（主动画画）

机器人主动说出画图意图时，自动生成图片。

**触发示例**：
- "我想画一片星空"
- "让我试试画一只猫"
- "我会尝试画一片草原"
- "来一张夕阳的图"

**不会触发**：
- "哇，真的画出来了，好漂亮"（评价）
- "画得真好"（夸奖）

### 3. 快捷指令

```
/sd画 一只猫，在草地上奔跑
```

### 4. 查询作品集

LLM 自动识别查询意图并调用 `recall_drawing` 工具：

**用户**: "我之前画的星空图还在吗？"  
**机器人**: 查找并发送匹配的图片

### 5. 供其他插件调用

```python
# 在其他插件中
inkfusion = await context.get_star("astrbot_plugin_inkfusion")
if inkfusion:
    success, review = await inkfusion.draw(event, "一只可爱的猫")
```

---

## 🔧 工作流程

```
用户发送消息
    ↓
LLM 判断是否为画图意图 / 工具调用
    ↓
是 → 优化提示词 → 调用 SD API → 发送图片 → 保存作品集
    ↓
否 → 忽略
```

---

## 📂 作品集目录结构

```
./sd_images_gallery/
├── 20250423_星空下的猫_20250423_143025.png
├── 20250423_草原_20250423_150310.png
├── gallery_index.json          # 索引文件
└── ...
```

### gallery_index.json 格式

```json
[
  {
    "filename": "20250423_星空下的猫_20250423_143025.png",
    "date": "20250423",
    "timestamp": "20250423_143025",
    "original_prompt": "星空下的猫",
    "optimized_prompt": "a cat sitting under the starry night sky...",
    "short_content": "星空下的猫"
  }
]
```

---

## 📝 人格提示词建议

为了让机器人主动提出画画，建议在人格设定中添加以下内容：

```markdown
【画图能力】
你可以生成图片。当你想表达某个画面时，可以说出类似的话：

- "我想画一片星空"
- "让我试试画一只猫"
- "我会尝试画一片草原"
- "来一张夕阳的图"

当你这样说的时候，图片会自动出现。不用解释，不用等。
```

---

## 🔧 与原项目的差异

| 功能 | 原项目 | 本版本 |
|------|--------|--------|
| 主动画画（自动触发） | ✅ 支持 | ✅ 保留 |
| 提示词优化 | ✅ 支持 | ✅ 保留并优化 |
| 视觉评价 | ✅ 支持 | ❌ 已禁用 |
| 作品集保存 | ✅ 支持 | ✅ 保留并优化 |
| LLM 工具调用 | 部分 | ✅ 完整实现 |
| 图片 URL 生成 | ✅ 支持 | ❌ 已移除 |
| 作品集查询 | ❌ 无 | ✅ 新增 |

### 主要修改

1. **移除视觉评价功能** - 简化流程，减少依赖
2. **优化提示词构建** - 用户描述始终在最前面
3. **完善 LLM 工具调用** - 更详细的工具描述
4. **新增作品集查询** - 支持关键词和日期检索
5. **改进日志输出** - 更清晰的调试信息
6. **移除图片 URL 生成** - 专注核心功能

---

## ❓ 常见问题

### Q1：为什么说"画得真好"也会触发？
新版已使用 LLM 意图判断，评价类语句不会触发。确保已更新到最新版本。

### Q2：图片生成很慢？
- 降低 `sd_steps`（如改为 15）
- 降低图片分辨率
- 升级显卡或使用更快的模型

### Q3：SD API 连接失败？
- 确认 SD WebUI 已启动
- 确认启动参数包含 `--api`
- 检查 `sd_base_url` 是否正确
- 尝试在浏览器访问 `http://127.0.0.1:7860/docs` 确认 API 可用

### Q4：机器人不说画画相关的话怎么办？
在人格设定中添加画图能力的说明。参考上方的「人格提示词建议」。

### Q5：作品集保存位置在哪？
默认在 `./sd_images_gallery`，可在配置中修改 `local_save_path`。

### Q6：如何查看插件是否正常工作？
观察控制台日志，应看到类似输出：

```
[纯SD绘画引擎] SD: 开 | 作品集: 开 | 提示词优化: 开
[画图工具] 收到画图请求: 星空下的猫
SD 图片生成成功: /tmp/sd_images/xxx.png
[作品集] 图片已保存: ./sd_images_gallery/20250423_星空下的猫_xxx.png
```

---

## 📄 许可证

本项目使用 **GNU Affero General Public License v3.0 (AGPL-3.0)** 授权。

- 原始项目: [astrbot_plugin_inkfusion](https://github.com/fatsnk/astrbot_plugin_inkfusion) by F5
- 修改作者: Nekoviet13
- 修改日期: 2026-06-21

**AGPL 合规性**：
- ✅ 源代码完全公开
- ✅ 所有修改明确标注
- ✅ 保留原始版权声明
- ✅ 使用相同的 AGPL 许可证
- ✅ 通过网络使用，用户有权获取源代码

完整许可证文本请查看 [LICENSE](./LICENSE) 文件。

---

## 🔗 相关链接

- [原项目 - astrbot_plugin_inkfusion](https://github.com/fatsnk/astrbot_plugin_inkfusion)
- [AGPL 许可证全文](https://www.gnu.org/licenses/agpl-3.0.txt)
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
- [AstrBot 文档](https://astrbot.app)

---

## 🤝 贡献

本项目基于 AGPL 许可证，欢迎提交 Issue 和 Pull Request。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing`)
3. 提交修改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing`)
5. 创建 Pull Request

---

## ⚠️ 免责声明

- 请确保 Stable Diffusion WebUI 已正确配置并运行
- 生成的图片内容由提示词决定，请遵守相关法律法规
- 本插件仅供学习研究使用