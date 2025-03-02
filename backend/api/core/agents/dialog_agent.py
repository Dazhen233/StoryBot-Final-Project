# core/agents/dialog_agent.py
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import openai
from pydantic import BaseModel
from jinja2 import Environment, BaseLoader
from app.core.memory import SessionManager
from app.config.settings import settings
from app.models.schemas import DialogEvaluation

logger = logging.getLogger("dialog_agent")

# ======================
# 数据模型
# ======================
class DialogInput(BaseModel):
    user_input: str
    character: str
    session_id: str

class DialogResponse(BaseModel):
    text_response: str
    audio_url: str
    next_prompt: str
    new_words: List[str]
    difficulty_level: int

# ======================
# 提示词模板
# ======================
DIALOG_PROMPT_TEMPLATE = """
你是一个儿童英语教学助手，正在与{{ age }}岁儿童进行互动对话。请根据以下信息生成回应：

# 当前会话状态
- 角色：{{ character }}（{{ character_desc }}）
- 已学词汇：{{ known_words|join(', ') }}
- 当前故事进度：{{ current_story[:100] }}...

# 用户输入
用户说："{{ user_input }}"

# 任务要求
1. 评估英语水平（1-5级）
2. 生成符合{{ target_level }}级的回应
3. 包含1-2个新词汇：{{ new_words|join(', ') }}
4. 提出引导性问题（用[QUESTION]标记）
5. 使用简单疑问句鼓励继续对话

# 输出格式
{
  "response": "回应文本",
  "next_prompt": "引导问题",
  "new_words": ["单词1", "单词2"],
  "assessed_level": 等级
}
"""

# ======================
# 对话评估智能体
# ======================
class DialogAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_manager = SessionManager()
        self.env = Environment(loader=BaseLoader())
        self.template = self.env.from_string(DIALOG_PROMPT_TEMPLATE)

    async def evaluate_and_respond(self, input: DialogInput) -> DialogResponse:
        """处理用户输入并生成教学响应"""
        try:
            # 获取会话上下文
            context = await self._get_dialog_context(input)
            
            # 生成提示词
            prompt = self._build_prompt(context)
            
            # 调用大模型
            raw_response = await self._call_llm(prompt)
            
            # 解析响应
            dialog_data = self._parse_response(raw_response)
            
            # 生成语音
            audio_url = await self._generate_speech(dialog_data.response)
            
            # 更新会话状态
            await self._update_session_state(dialog_data, context)
            
            return DialogResponse(
                text_response=dialog_data.response,
                audio_url=audio_url,
                next_prompt=dialog_data.next_prompt,
                new_words=dialog_data.new_words,
                difficulty_level=dialog_data.assessed_level
            )
            
        except Exception as e:
            logger.error(f"Dialog processing failed: {str(e)}")
            return self._generate_fallback_response()

    async def _get_dialog_context(self, input: DialogInput) -> Dict:
        """获取对话上下文"""
        session = await self.session_manager.get_session(self.session_id)
        character_desc = self._get_character_desc(input.character)
        
        return {
            "age": session.user_age,
            "character": input.character,
            "character_desc": character_desc,
            "known_words": session.vocabulary,
            "current_story": session.story_progress,
            "user_input": input.user_input,
            "target_level": self._calculate_target_level(session),
            "new_words": self._select_new_words(session)
        }

    def _build_prompt(self, context: Dict) -> str:
        """构建对话提示词"""
        return self.template.render(**context)

    async def _call_llm(self, prompt: str) -> str:
        """调用大模型接口"""
        response = await openai.ChatCompletion.acreate(
            model=settings.openai.dialog_model,
            messages=[
                {"role": "system", "content": "你是一个儿童英语教学专家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )
        return response.choices[0].message['content']

    def _parse_response(self, raw_response: str) -> DialogEvaluation:
        """解析大模型响应"""
        try:
            data = json.loads(raw_response)
            return DialogEvaluation(
                response=data["response"],
                next_prompt=data["next_prompt"],
                new_words=data["new_words"],
                assessed_level=data["assessed_level"]
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid dialog response: {raw_response}")
            raise ValueError("LLM response format error") from e

    async def _generate_speech(self, text: str) -> str:
        """生成角色语音"""
        try:
            response = await openai.Audio.acreate(
                model=settings.openai.tts_model,
                input=text,
                voice=self._get_voice_style(),
                speed=0.85
            )
            return response.url
        except Exception as e:
            logger.error(f"TTS failed: {str(e)}")
            return ""

    async def _update_session_state(self, data: DialogEvaluation, context: Dict):
        """更新学习进度"""
        updates = {
            "vocabulary": list(set(context["known_words"] + data.new_words)),
            "difficulty_level": data.assessed_level,
            "last_interaction": datetime.now()
        }
        await self.session_manager.update_session(self.session_id, updates)

    # ======================
    # 辅助方法
    # ======================
    def _get_character_desc(self, character: str) -> str:
        """获取角色描述"""
        descriptions = {
            "elsa": "冰雪女王，喜欢用冰雪魔法帮助朋友",
            "mickey": "乐观好奇的老鼠，经常探索新事物",
            "paw_patrol": "救援小狗团队，勇敢热心"
        }
        return descriptions.get(character.lower(), "友好的卡通角色")

    def _calculate_target_level(self, session) -> int:
        """计算目标难度级别"""
        # 基于历史表现的简单算法
        base_level = session.difficulty_level
        error_rate = session.error_count / (session.interaction_count + 1)
        
        if error_rate < 0.2:
            return min(base_level + 1, 5)
        elif error_rate > 0.5:
            return max(base_level - 1, 1)
        else:
            return base_level

    def _select_new_words(self, session) -> List[str]:
        """选择本次教学的新词"""
        all_words = settings.vocabulary_by_level[session.difficulty_level]
        return [w for w in all_words if w not in session.vocabulary][:2]

    def _get_voice_style(self) -> str:
        """获取语音风格"""
        # 根据角色返回预定义的语音风格
        return "nova"

    def _generate_fallback_response(self) -> DialogResponse:
        """生成降级响应"""
        return DialogResponse(
            text_response="Let's try that again! What would you like to do next?",
            audio_url="",
            next_prompt="Choose an action: [1] Continue story [2] Repeat",
            new_words=[],
            difficulty_level=1
        )