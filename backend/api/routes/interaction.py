from fastapi import APIRouter, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import base64
import logging
from datetime import datetime

# 自定义模块导入
from app.core.agents import DialogEvaluator
from app.core.memory.session_manager import SessionManager
from app.core.rendering import AudioProcessor
from app.models.schemas import InteractionResponse
from app.models.database import get_db
from app.config.settings import settings

router = APIRouter(prefix="/interaction", tags=["Interaction"])
logger = logging.getLogger("interaction")

# ======================
# 数据模型
# ======================
class VoiceInput(BaseModel):
    session_id: str
    audio_base64: str  # base64编码的音频文件
    character: str

class TextInput(BaseModel):
    session_id: str
    user_input: str
    character: str

class ProgressResponse(BaseModel):
    session_id: str
    vocabulary: list
    progress: dict
    interaction_count: int

# ======================
# 核心路由
# ======================
@router.post("/voice", response_model=InteractionResponse)
async def handle_voice_interaction(input: VoiceInput):
    """
    处理语音输入并生成互动响应
    
    参数:
    - session_id: 当前会话ID
    - audio_base64: base64编码的音频数据（支持wav/mp3）
    - character: 选择的动漫角色
    
    返回:
    - text_response: 文本回复
    - audio_url: 生成的语音URL
    - next_prompt: 后续引导问题
    - new_words: 本次互动的新单词
    """
    try:
        # 解码音频
        audio_data = base64.b64decode(input.audio_base64)
        text = await AudioProcessor.speech_to_text(audio_data)
        
        # 获取会话上下文
        db = next(get_db())
        session = SessionManager(db).get_session(input.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 评估对话内容
        evaluator = DialogEvaluator(
            character=input.character,
            age_group=session.age_group,
            history=session.interaction_history
        )
        
        # 生成互动响应
        response = await evaluator.generate_response(
            user_input=text,
            current_story=session.story_progress
        )
        
        # 更新会话状态
        SessionManager(db).update_session(
            session_id=input.session_id,
            updates={
                "interaction_count": session.interaction_count + 1,
                "vocabulary": list(set(session.vocabulary + response.new_words)),
                "last_interaction": datetime.now()
            }
        )
        
        # 生成语音
        audio_url = await AudioProcessor.text_to_speech(
            text=response.text_response,
            character=input.character
        )
        
        return {
            "text_response": response.text_response,
            "audio_url": audio_url,
            "next_prompt": response.next_prompt,
            "new_words": response.new_words
        }
        
    except Exception as e:
        logger.error(f"Voice interaction failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Interaction error: {str(e)}"}
        )

@router.post("/text", response_model=InteractionResponse)
async def handle_text_interaction(input: TextInput):
    """
    处理文本输入并生成互动响应
    
    参数:
    - session_id: 当前会话ID
    - user_input: 用户输入的文本
    - character: 选择的动漫角色
    
    返回:
    - text_response: 文本回复
    - audio_url: 生成的语音URL
    - next_prompt: 后续引导问题
    - new_words: 本次互动的新单词
    """
    try:
        db = next(get_db())
        session = SessionManager(db).get_session(input.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        evaluator = DialogEvaluator(
            character=input.character,
            age_group=session.age_group,
            history=session.interaction_history
        )
        
        response = await evaluator.generate_response(
            user_input=input.user_input,
            current_story=session.story_progress
        )
        
        # 更新会话状态
        SessionManager(db).update_session(
            session_id=input.session_id,
            updates={
                "interaction_count": session.interaction_count + 1,
                "vocabulary": list(set(session.vocabulary + response.new_words)),
                "last_interaction": datetime.now()
            }
        )
        
        audio_url = await AudioProcessor.text_to_speech(
            text=response.text_response,
            character=input.character
        )
        
        return {
            "text_response": response.text_response,
            "audio_url": audio_url,
            "next_prompt": response.next_prompt,
            "new_words": response.new_words
        }
        
    except Exception as e:
        logger.error(f"Text interaction failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Interaction error: {str(e)}"}
        )

@router.get("/progress/{session_id}", response_model=ProgressResponse)
async def get_interaction_progress(session_id: str):
    """
    获取用户互动进度
    
    参数:
    - session_id: 需要查询的会话ID
    
    返回:
    - vocabulary: 已学习的词汇列表
    - progress: 当前故事进度
    - interaction_count: 互动次数
    """
    try:
        db = next(get_db())
        session = SessionManager(db).get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return {
            "session_id": session_id,
            "vocabulary": session.vocabulary,
            "progress": session.story_progress,
            "interaction_count": session.interaction_count
        }
    except Exception as e:
        logger.error(f"Progress query failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Failed to get progress"}
        )