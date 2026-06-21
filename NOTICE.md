# NOTICE - 版权和归属信息

## 本项目包含以下第三方代码：

### astrbot_plugin_inkfusion (原始项目)

- **项目名称**: astrbot_plugin_inkfusion
- **版权所有者**: F5 (fatsnk)
- **许可证**: GNU Affero General Public License v3.0
- **原始来源**: https://github.com/fatsnk/astrbot_plugin_inkfusion
- **项目描述**: AI图片生成插件，支持主动画画、提示词优化和视觉评价

---

## 本修改版本信息

- **项目名称**: astrbot_plugin_inkfusion (客制化版本)
- **修改作者**: Nekoviet13
- **联系邮箱**: 1213733068@qq.com
- **修改日期**: 2026-06-21
- **基于版本**: 原始 astrbot_plugin_inkfusion
- **许可证**: GNU Affero General Public License v3.0

---

## 主要修改内容

| 修改项 | 说明 |
|--------|------|
| **移除视觉评价功能** | 禁用 `enable_vision_review` 相关代码，简化流程 |
| **优化提示词构建** | 用户描述始终在提示词最前面 (`_build_sd_prompt`) |
| **完善 LLM 工具调用** | 增强 `draw_picture` 工具描述，提高 LLM 识别率 |
| **新增作品集查询** | 添加 `recall_drawing` 工具，支持关键词/日期检索 |
| **改进日志输出** | 增加更详细的调试日志，方便问题排查 |
| **移除图片 URL 生成** | 删除 `_generate_image_url` 相关代码 |
| **代码风格优化** | 统一代码格式和注释 |

---

## 文件修改清单

### main.py（核心插件代码）

#### 移除的功能
- `_review_image()` - 图片视觉评价
- `enable_vision_review` - 视觉评价开关
- `vision_provider_id` - 视觉评价 Provider
- `vision_review_prompt` - 评价提示词
- `review_send_mode` - 评价发送模式
- `_generate_image_url()` - 图片 URL 生成
- `_build_image_url()` - URL 构建辅助

#### 新增的功能
- `recall_drawing_tool()` - 作品集查询工具
- `_send_gallery_images()` - 批量发送图片

#### 修改的功能
- `_build_sd_prompt()` - 用户描述始终在最前面
- `draw()` - 移除 URL 返回，简化逻辑
- `draw_picture_tool()` - 增强工具描述
- `_save_to_gallery()` - 优化保存逻辑

---

## 第三方依赖

本项目依赖以下第三方库：

| 库名 | 版本要求 | 用途 | 许可证 |
|------|----------|------|--------|
| aiohttp | >=3.8.0 | HTTP 客户端 | Apache 2.0 |
| astrbot-api | >=4.0.0 | AstrBot 框架 API | MIT |
| Python 标准库 | >=3.8 | 基础功能 | Python License |

---

## 版权声明
