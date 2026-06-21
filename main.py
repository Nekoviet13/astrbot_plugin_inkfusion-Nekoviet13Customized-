"""
SDInkfusion
基于原项目修改 (Original Project: [astrbot_plugin_inkfusion])

Copyright (C) 2026 [Nekoviet13] <[1213733068@qq.com]>
Original Copyright (C) [F5]

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import re
import ssl
import uuid
import json
import time
import random
import asyncio
import tempfile
import shutil
import base64
import urllib.parse
import aiohttp
from datetime import datetime
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.core.star.star_tools import StarTools


@register(
    "astrbot_plugin_inkfusion",
    "F5 Nekoviet13",
    "纯SD绘画引擎，主动让机器人识别用户绘画意图，提供画图API供其他插件调用",
    "4.3.0",
    "https://github.com/fatsnk/astrbot_plugin_inkfusion"
)
class InkfusionPlugin(Star):
    """
    纯 Stable Diffusion  绘画引擎。
    """

    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config

        # 临时图片存储目录
        self.temp_dir = os.path.join(tempfile.gettempdir(), "sd_images")
        os.makedirs(self.temp_dir, exist_ok=True)

        # Stable Diffusion 配置
        self.sd_enabled: bool = self.config.get("sd_enabled", False)
        self.sd_skip_ssl_verify: bool = self.config.get("sd_skip_ssl_verify", False)
        self.sd_base_url: str = self.config.get("sd_base_url", "http://127.0.0.1:7860").rstrip("/")
        self.sd_width: int = self.config.get("sd_width", 512)
        self.sd_height: int = self.config.get("sd_height", 512)
        self.sd_positive_prompt: str = self.config.get("sd_positive_prompt", "masterpiece, best quality, {{positive}}")
        self.sd_negative_prompt: str = self.config.get("sd_negative_prompt", "bad quality, worst quality, low quality, blurry, bad anatomy, bad hands, extra digits")
        self.sd_steps: int = self.config.get("sd_steps", 20)
        self.sd_cfg_scale: float = float(self.config.get("sd_cfg_scale", 7.0))
        self.sd_sampler_name: str = self.config.get("sd_sampler_name", "Euler a")
        self.sd_scheduler: str = self.config.get("sd_scheduler", "")
        self.sd_seed: int = self.config.get("sd_seed", -1)
        self.sd_restore_faces: bool = self.config.get("sd_restore_faces", False)
        self.sd_model_checkpoint: str = self.config.get("sd_model_checkpoint", "")
        self.sd_clip_skip: int = self.config.get("sd_clip_skip", 0)

        # 提示词优化配置
        self.enable_prompt_optimization: bool = self.config.get("enable_prompt_optimization", True)
        self.prompt_provider_name: str = self.config.get("prompt_provider_name", "")
        self.optimization_system_prompt: str = self.config.get(
            "optimization_system_prompt",
            "You are an expert in crafting prompts for AI image generation models. "
            "Your task is to take a user's simple idea and transform it into a rich, detailed, and artistic prompt in English. "
            "The final output should be a single, continuous string of keywords and descriptions, separated by commas. "
            "Do not add any other explanatory text, just the prompt itself. "
            "Focus on visual details, art style (e.g., photorealistic, watercolor, anime), composition, and lighting."
        )

        # 视觉评价配置（已禁用）
        self.enable_vision_review: bool = self.config.get("enable_vision_review", False)
        self.vision_provider_id: str = self.config.get("vision_provider_id", "")
        self.vision_review_prompt: str = self.config.get("vision_review_prompt", "请用一句话评价这张图片，语气要自然、友善，像朋友聊天一样。")
        self.review_send_mode: str = self.config.get("review_send_mode", "separate")

        # 作品集配置
        self.enable_local_save: bool = self.config.get("enable_local_save", False)
        self.local_save_path: str = self.config.get("local_save_path", "./sd_images_gallery")
        self.save_with_prompt: bool = self.config.get("save_with_prompt", True)

        if self.enable_local_save:
            os.makedirs(self.local_save_path, exist_ok=True)
            logger.info(f"[作品集] 保存目录: {os.path.abspath(self.local_save_path)}")

        logger.info(f"纯SD绘画引擎已加载 | SD: {'开' if self.sd_enabled else '关'} | 作品集: {'开' if self.enable_local_save else '关'} | 提示词优化: {'开' if self.enable_prompt_optimization else '关'}")

    def _get_sd_connector(self) -> aiohttp.TCPConnector:
        if self.sd_skip_ssl_verify:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            return aiohttp.TCPConnector(ssl=ssl_ctx)
        return aiohttp.TCPConnector()

    def _build_sd_prompt(self, user_prompt: str) -> str:
        """将用户提示词填入 SD 正面提示词模板，用户描述始终在前"""
        template = self.sd_positive_prompt
        
        if "{{positive}}" in template:
            base = template.replace("{{positive}}", "").strip()
            base = base.rstrip(',').strip()
            if base:
                result = f"{user_prompt}, {base}"
            else:
                result = user_prompt
        else:
            result = f"{user_prompt}, {template}" if template else user_prompt
        
        logger.debug(f"[提示词构建] 最终提示词: {result[:100]}...")
        return result

    async def _optimize_prompt(self, theme: str) -> str:
        if not self.enable_prompt_optimization:
            return theme
        provider = None
        if self.prompt_provider_name:
            provider = self.context.get_provider_by_id(self.prompt_provider_name)
        if not provider:
            provider = self.context.get_using_provider()
        if not provider:
            return theme
        try:
            llm_response = await provider.text_chat(
                prompt=f"User's idea: {theme}",
                system_prompt=self.optimization_system_prompt,
                contexts=[],
                temperature=0.7
            )
            if llm_response and llm_response.completion_text:
                return llm_response.completion_text.strip()
        except Exception as e:
            logger.error(f"提示词优化失败: {e}")
        return theme

    async def _generate_image_sd(self, prompt_text: str) -> str:
        endpoint = f"{self.sd_base_url}/sdapi/v1/txt2img"
        positive = self._build_sd_prompt(prompt_text)

        sd_params = {
            "prompt": positive,
            "negative_prompt": self.sd_negative_prompt,
            "steps": self.sd_steps,
            "cfg_scale": self.sd_cfg_scale,
            "width": self.sd_width,
            "height": self.sd_height,
            "sampler_name": self.sd_sampler_name,
            "seed": self.sd_seed,
            "restore_faces": self.sd_restore_faces,
        }

        if self.sd_scheduler:
            sd_params["scheduler"] = self.sd_scheduler

        override_settings = {}
        if self.sd_model_checkpoint:
            override_settings["sd_model_checkpoint"] = self.sd_model_checkpoint
        if self.sd_clip_skip and self.sd_clip_skip > 0:
            override_settings["CLIP_stop_at_last_layers"] = self.sd_clip_skip

        if override_settings:
            sd_params["override_settings"] = override_settings
            sd_params["override_settings_restore_afterwards"] = True

        logger.info(f"SD 请求: {endpoint}")

        try:
            connector = self._get_sd_connector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    endpoint,
                    json=sd_params,
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"SD API 错误 {resp.status}: {error_text[:200]}")

                    data = await resp.json()
                    images = data.get("images", [])
                    if not images:
                        raise Exception("SD API 返回数据中没有图片")

                    image_bytes = base64.b64decode(images[0])
                    filename = f"{uuid.uuid4().hex}.png"
                    filepath = os.path.join(self.temp_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)

                    logger.info(f"SD 图片生成成功: {filepath}")
                    return filepath

        except aiohttp.ClientError as e:
            raise Exception(f"SD API 连接失败: {e}")
        except asyncio.TimeoutError:
            raise Exception("SD API 请求超时")

    async def _review_image(self, image_path: str) -> str:
        # 视觉评价已禁用，直接返回空
        return ""

    # ==================== 供其他插件调用的 API ====================

    async def draw(self, event: AstrMessageEvent, prompt: str) -> tuple:
        """供其他插件调用的画图接口
        返回 (success, review)
        """
        if not self.sd_enabled:
            logger.warning("[绘画引擎] SD未启用")
            return False, ""

        logger.info(f"[绘画引擎] 原始提示词: {prompt}")

        try:
            optimized_prompt = await self._optimize_prompt(prompt)
            logger.info(f"[绘画引擎] 优化后提示词: {optimized_prompt[:150]}...")
            
            image_path = await self._generate_image_sd(optimized_prompt)

            self._save_to_gallery(image_path, prompt, optimized_prompt)

            # 视觉评价已禁用
            review = ""

            await event.send(event.image_result(image_path))

            logger.info("[绘画引擎] 图片生成成功并发送")
            return True, review
        except Exception as e:
            logger.error(f"[绘画引擎] 生图失败: {e}")
            return False, ""

    # ==================== 作品集辅助方法 ====================

    def _save_to_gallery(self, image_path: str, original_prompt: str, optimized_prompt: str = ""):
        if not self.enable_local_save:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_str = datetime.now().strftime("%Y%m%d")
            
            short_content = original_prompt[:15].strip()
            short_content = re.sub(r'[\\/*?:"<>|]', '', short_content)
            
            filename = f"{date_str}_{short_content}_{timestamp}.png"
            save_path = os.path.join(self.local_save_path, filename)
            
            shutil.copy2(image_path, save_path)
            logger.info(f"[作品集] 图片已保存: {save_path}")
            
            index_file = os.path.join(self.local_save_path, "gallery_index.json")
            index_data = []
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            
            index_data.append({
                "filename": filename,
                "date": date_str,
                "timestamp": timestamp,
                "original_prompt": original_prompt,
                "optimized_prompt": optimized_prompt,
                "short_content": short_content
            })
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"[作品集] 保存失败: {e}")

    async def _send_gallery_images(self, event: AstrMessageEvent, items: list):
        for item in items:
            image_path = os.path.join(self.local_save_path, item["filename"])
            if os.path.exists(image_path):
                await event.send(event.image_result(image_path))
                await asyncio.sleep(1)
            else:
                await event.send(event.plain_result(f"图片 {item['short_content']} 找不到了..."))

    # ==================== LLM 工具调用 ====================

    @filter.llm_tool(name="draw_picture")
    @filter.llm_tool(name="draw_picture")
    async def draw_picture_tool(self, event: AstrMessageEvent, prompt: str):
        """画图工具。**强制规则：当用户明确要求你「画图」、「画画」、「生成图片」、「画一张图」或任何与「视觉创作」相关的请求时，你绝对不能只用文字描述你在画什么。你必须调用此工具来真正生成图片。**
        
        调用示例：
        - 用户说「画一只猫」→ 调用 draw_picture(prompt="一只猫")
        - 用户说「帮我画个星空」→ 调用 draw_picture(prompt="星空，星星闪烁，银河")
        
        Args:
            prompt(str): 用户想要画的内容描述，用中文。要详细、具体。
        """
        logger.info(f"[画图工具] 收到画图请求: {prompt}")
        
        success, review = await self.draw(event, prompt)
        
        if success:
            if review:
                return f"画好了！{review} 这是你想要的{prompt}"
            else:
                return f"画好了！这是你想要的{prompt}"
        else:
            return f"画图失败了，请稍后再试"

    @filter.llm_tool(name="recall_drawing")
    async def recall_drawing_tool(self, event: AstrMessageEvent, keyword: str = "", date: str = ""):
        """回忆以前画的画。根据关键词或日期查找并发送图片。
        
        Args:
            keyword(str): 要搜索的关键词，如"星空"、"草原"、"猫"等
            date(str): 日期，格式 YYYYMMDD，如 20250423
        """
        if not self.enable_local_save:
            return "作品集功能未启用，请在配置中开启。"
        
        index_file = os.path.join(self.local_save_path, "gallery_index.json")
        if not os.path.exists(index_file):
            return "还没有画过任何画呢，要不先让我画一张？"
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        if not index_data:
            return "作品集是空的，还没有画过画。"
        
        matched = []
        for item in index_data:
            if date and item.get("date") != date:
                continue
            if keyword and keyword not in item.get("original_prompt", "") and keyword not in item.get("short_content", ""):
                continue
            matched.append(item)
        
        if not matched:
            if date:
                return f"没有找到 {date} 画的画。"
            else:
                return f"没有找到包含「{keyword}」的画。"
        
        matched = matched[-3:]
        
        result = f"找到了 {len(matched)} 幅画：\n"
        for item in matched:
            result += f"- {item['short_content']}（{item['date']}）\n"
        result += "\n正在为你发送..."
        
        asyncio.create_task(self._send_gallery_images(event, matched))
        
        return result

    # ==================== 指令（调试用） ====================

    @filter.command("sd画")
    async def sd_generate_shortcut(self, event: AstrMessageEvent, prompt_text: str = ""):
        if not self.sd_enabled:
            yield event.plain_result("Stable Diffusion 未启用")
            return

        full_prompt = event.message_str.strip()
        if full_prompt.startswith('/sd画 '):
            prompt_text = full_prompt[6:].strip()
        elif full_prompt.startswith('/sd画'):
            prompt_text = full_prompt[5:].strip()

        if not prompt_text:
            yield event.plain_result("请提供图片描述")
            return

        yield event.plain_result(f"正在生成图片...")

        try:
            optimized_prompt = await self._optimize_prompt(prompt_text)
            image_path = await self._generate_image_sd(optimized_prompt)
            self._save_to_gallery(image_path, prompt_text, optimized_prompt)
            yield event.image_result(image_path)
        except Exception as e:
            yield event.plain_result(f"生图失败: {str(e)}")

    async def terminate(self):
        logger.info("纯SD绘画引擎已卸载。")
