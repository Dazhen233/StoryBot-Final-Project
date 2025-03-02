# core/rendering/image_controller.py
import os
import logging
import base64
import requests
from io import BytesIO
from typing import Optional, Union
from pydantic import BaseModel
from app.config.settings import settings
from app.core.memory import SessionManager

logger = logging.getLogger("image_controller")

# ======================
# 数据模型
# ======================
class ImageGenerationInput(BaseModel):
    prompt: str
    negative_prompt: str = "ugly, blurry, disfigured"
    control_image: Optional[Union[str, bytes]] = None  # base64或bytes
    width: int = 1920
    height: int = 1080
    samples: int = 1
    steps: int = 30

class ImageGenerationOutput(BaseModel):
    image_url: Optional[str]
    image_data: Optional[bytes]
    debug_info: dict

# ======================
# 基础渲染策略
# ======================
class RenderingStrategy:
    async def render(self, input: ImageGenerationInput) -> ImageGenerationOutput:
        raise NotImplementedError

# ======================
# ControlNet 策略
# ======================
class ControlNetRenderer(RenderingStrategy):
    def __init__(self):
        self.api_host = "https://api.stability.ai"
        self.engine_id = "stable-diffusion-xl-1024-v1-0"
        self.api_key = settings.stability_api_key

    async def render(self, input: ImageGenerationInput) -> ImageGenerationOutput:
        try:
            # 准备姿势图像
            control_image = self._process_control_image(input.control_image)
            
            response = requests.post(
                f"{self.api_host}/v1/generation/{self.engine_id}/image-to-image",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
                files={
                    "init_image": control_image,
                },
                data={
                    "image_strength": 0.35,
                    "init_image_mode": "IMAGE_STRENGTH",
                    "text_prompts[0][text]": input.prompt,
                    "text_prompts[0][weight]": 1.0,
                    "text_prompts[1][text]": input.negative_prompt,
                    "text_prompts[1][weight]": -1.0,
                    "cfg_scale": 7,
                    "samples": input.samples,
                    "steps": input.steps,
                    "style_preset": "digital-art"
                }
            )

            if response.status_code != 200:
                raise Exception(f"ControlNet API error: {response.text}")

            data = response.json()
            image_data = base64.b64decode(data["artifacts"][0]["base64"])

            return ImageGenerationOutput(
                image_data=image_data,
                debug_info={
                    "strategy": "controlnet",
                    "engine": self.engine_id
                }
            )

        except Exception as e:
            logger.error(f"ControlNet rendering failed: {str(e)}")
            return self._generate_fallback(input)

    def _process_control_image(self, image_input):
        """处理姿势引导图输入"""
        if isinstance(image_input, bytes):
            return BytesIO(image_input)
        elif image_input.startswith("data:image"):
            return BytesIO(base64.b64decode(image_input.split(",")[1]))
        else:
            raise ValueError("Invalid control image format")

# ======================
# LoRA 策略
# ======================
class LoRARenderer(RenderingStrategy):
    def __init__(self):
        self.api_host = "https://api.stability.ai"
        self.api_key = settings.stability_api_key
        self.lora_model_id = "user-lora-123"  # 预先训练好的LoRA模型ID

    async def render(self, input: ImageGenerationInput) -> ImageGenerationOutput:
        try:
            response = requests.post(
                f"{self.api_host}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text_prompts": [
                        {"text": f"<lora:{self.lora_model_id}> {input.prompt}", "weight": 1},
                        {"text": input.negative_prompt, "weight": -1}
                    ],
                    "cfg_scale": 7,
                    "height": input.height,
                    "width": input.width,
                    "samples": input.samples,
                    "steps": input.steps,
                    "style_preset": "digital-art"
                }
            )

            if response.status_code != 200:
                raise Exception(f"LoRA API error: {response.text}")

            data = response.json()
            image_data = base64.b64decode(data["artifacts"][0]["base64"])

            return ImageGenerationOutput(
                image_data=image_data,
                debug_info={
                    "strategy": "lora",
                    "model_id": self.lora_model_id
                }
            )

        except Exception as e:
            logger.error(f"LoRA rendering failed: {str(e)}")
            return self._generate_fallback(input)

# ======================
# 统一图像控制器
# ======================
class ImageRenderer:
    def __init__(self, strategy: str = "controlnet"):
        """
        初始化渲染器
        
        参数:
            strategy: 
                - "controlnet" (默认): 使用姿势控制生成
                - "lora": 使用自定义角色LoRA模型
        """
        self.strategy = strategy.lower()
        self.impl = self._initialize_strategy()

    def _initialize_strategy(self) -> RenderingStrategy:
        if self.strategy == "controlnet":
            return ControlNetRenderer()
        elif self.strategy == "lora":
            return LoRARenderer()
        else:
            raise ValueError(f"不支持的渲染策略: {self.strategy}")

    async def render(self, 
                   prompt: str,
                   control_image: Optional[Union[str, bytes]] = None,
                   negative_prompt: str = "ugly, blurry, disfigured",
                   width: int = 1920,
                   height: int = 1080) -> ImageGenerationOutput:
        """
        生成图像的统一接口
        
        参数:
            prompt: 生成提示词
            control_image: 姿势引导图 (ControlNet必需)
            negative_prompt: 负面提示词
            width: 图像宽度
            height: 图像高度
            
        返回:
            ImageGenerationOutput 包含图像数据和调试信息
        """
        input = ImageGenerationInput(
            prompt=prompt,
            negative_prompt=negative_prompt,
            control_image=control_image,
            width=width,
            height=height
        )
        
        return await self.impl.render(input)

    @staticmethod
    def _generate_fallback(input: ImageGenerationInput) -> ImageGenerationOutput:
        """生成备用图像"""
        logger.warning("Using fallback image")
        return ImageGenerationOutput(
            image_url=settings.fallback_image_url,
            debug_info={
                "error": "渲染失败，使用备用图像",
                "input": input.dict()
            }
        )

# ======================
# 使用示例
# ======================
async def example_usage():
    # 初始化渲染器
    renderer = ImageRenderer(strategy="controlnet")
    
    # 从会话获取上一次的姿势图
    session_manager = SessionManager()
    last_image = await session_manager.get_last_pose_image("session_123")
    
    # 生成图像
    result = await renderer.render(
        prompt="Elsa is building a snow castle, Disney style",
        control_image=last_image,
        width=1920,
        height=1080
    )
    
    if result.image_data:
        with open("output.png", "wb") as f:
            f.write(result.image_data)