# core/agents/story_agent.py
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
import openai
from pydantic import BaseModel
from jinja2 import Environment, BaseLoader
from app.core.rendering import ImageRenderer
from app.core.memory import SessionManager
from app.config.settings import settings
from app.models.schemas import StorySegment

logger = logging.getLogger("story_agent")

# ======================
# 数据模型
# ======================
class StoryGenerationInput(BaseModel):
    current_story: Optional[str]
    vocabulary_level: List[str]
    character: str
    last_choices: List[str] = []

class StoryGenerationOutput(BaseModel):
    story_text: str
    choices: List[str]
    target_words: List[str]
    image_prompt: str

# ======================
# 提示词模板
# ======================
STORY_PROMPT_TEMPLATE = """
你是一个儿童故事创作专家，正在为{{ age }}岁儿童创作英语学习故事。请根据以下要求生成故事段落：

# 角色设定
- 主要角色：{{ character }}（来自{{ character_source }}）
- 当前故事进度：{{ current_story[:100] }}...（继续发展）

# 创作要求
1. 必须包含以下{{ target_word_count }}个新词汇：[{{ target_words|join(', ') }}]
2. 使用简单句（最多8个单词）和现在进行时
3. 包含2个互动选项（用[CHOICE]标记）
4. 在故事中自然重复已学词汇：{{ existing_vocab|join(', ') }}

# 输出格式
用JSON格式返回：
{
  "story_text": "故事文本（包含[CHOICE]标记）",
  "choices": ["选项1", "选项2"],
  "target_words": ["单词1", "单词2"]
}
"""

# ======================
# 故事生成智能体
# ======================
class StoryAgent:
    def __init__(self, session_id: str, character: str):
        self.session_id = session_id
        self.character = character
        self.renderer = ImageRenderer(strategy="controlnet")
        self.session_manager = SessionManager()
        
        # 初始化模板引擎
        self.env = Environment(loader=BaseLoader())
        self.template = self.env.from_string(STORY_PROMPT_TEMPLATE)
    
    async def generate_next_segment(self) -> StorySegment:
        """生成下一个故事段落"""
        try:
            # 获取会话上下文
            context = await self._get_generation_context()
            
            # 生成提示词
            prompt = self._build_prompt(context)
            
            # 调用大模型
            raw_response = await self._call_llm(prompt)
            
            # 解析响应
            story_data = self._parse_response(raw_response)
            
            # 生成图片
            image_url = await self._generate_image(story_data.image_prompt)
            
            # 生成语音
            audio_url = await self._generate_speech(story_data.story_text)
            
            # 更新会话状态
            await self._update_session_state(story_data)
            
            return StorySegment(
                text=story_data.story_text,
                image_url=image_url,
                audio_url=audio_url,
                choices=story_data.choices,
                vocabulary=story_data.target_words
            )
            
        except Exception as e:
            logger.error(f"Story generation failed: {str(e)}")
            raise
    
    async def _get_generation_context(self) -> Dict:
        """获取故事生成上下文"""
        session = await self.session_manager.get_session(self.session_id)
        
        return {
            "age": session.user_age,
            "current_story": session.story_progress,
            "existing_vocab": session.vocabulary,
            "character_source": self._get_character_source(),
            "target_words": self._select_target_words(session),
            "target_word_count": 3  # 每次教3个新词
        }
    
    def _build_prompt(self, context: Dict) -> str:
        """构建大模型提示词"""
        return self.template.render(
            character=self.character,
            **context
        )
    
    async def _call_llm(self, prompt: str) -> str:
        """调用OpenAI接口"""
        response = await openai.ChatCompletion.acreate(
            model=settings.openai.story_model,
            messages=[
                {"role": "system", "content": "你是一个儿童英语教育专家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message['content']
    
    def _parse_response(self, raw_response: str) -> StoryGenerationOutput:
        """解析大模型响应"""
        try:
            data = json.loads(raw_response)
            return StoryGenerationOutput(
                story_text=data["story_text"],
                choices=data["choices"],
                target_words=data["target_words"],
                image_prompt=self._build_image_prompt(data["story_text"])
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {raw_response}")
            raise ValueError("Invalid LLM response format") from e
    
    def _build_image_prompt(self, story_text: str) -> str:
        """构建图片生成提示词"""
        return f"""
        {self.character} 正在故事场景中，风格：迪士尼卡通风格，
        场景描述：{story_text[:200]}...
        要求：
        - 保持角色一致性（参考角色设定图）
        - 明亮色彩和柔和的线条
        - 避免复杂细节
        """
    
    async def _generate_image(self, prompt: str) -> str:
        """生成故事图片"""
        try:
            # 获取角色基础姿势图
            base_image = await self.session_manager.get_last_image(self.session_id)
            
            return await self.renderer.render(
                prompt=prompt,
                control_image=base_image,  # 使用ControlNet保持一致性
                width=1920,
                height=1080
            )
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            return settings.fallback_image_url
    
    async def _generate_speech(self, text: str) -> str:
        """生成角色语音"""
        try:
            response = await openai.Audio.acreate(
                model=settings.openai.tts_model,
                input=text,
                voice=self._get_character_voice(),
                speed=0.9  # 适合儿童的语速
            )
            return response.url
        except Exception as e:
            logger.error(f"Speech synthesis failed: {str(e)}")
            return ""
    
    async def _update_session_state(self, data: StoryGenerationOutput):
        """更新会话状态"""
        updates = {
            "story_progress": data.story_text,
            "vocabulary": list(set(self.session.vocabulary + data.target_words)),
            "last_updated": datetime.now()
        }
        await self.session_manager.update_session(self.session_id, updates)
    
    # ======================
    # 辅助方法
    # ======================
    def _get_character_source(self) -> str:
        """获取角色来源信息"""
        character_map = {
            "elsa": "冰雪奇缘",
            "spongebob": "海绵宝宝",
            "paw_patrol": "汪汪队立大功"
        }
        return character_map.get(self.character.lower(), "经典卡通")
    
    def _select_target_words(self, session) -> List[str]:
        """选择本次教学的目标词汇"""
        # 实现词汇选择算法（示例使用简单随机选择）
        all_words = settings.vocabulary_lists[session.level]
        new_words = [w for w in all_words if w not in session.vocabulary]
        return new_words[:3]
    
    def _get_character_voice(self) -> str:
        """获取角色对应的语音风格"""
        voice_map = {
            "elsa": "alloy",
            "spongebob": "echo", 
            "paw_patrol": "nova"
        }
        return voice_map.get(self.character.lower(), "nova")