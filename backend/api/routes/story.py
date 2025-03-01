# api/routes/story.py
from fastapi import APIRouter, UploadFile
from app.core.agents import StoryAgent
from app.models.schemas import StoryRequest

router = APIRouter()

@router.post("/generate")
async def generate_story(request: StoryRequest):
    """统一故事生成入口"""
    agent = StoryAgent(
        session_id=request.session_id,
        character=request.character
    )
    
    # 异步生成所有内容
    result = await agent.generate(
        prompt=request.prompt,
        last_image=request.last_image  # 用于保持一致性
    )
    
    return {
        "text": result.story,
        "image": result.image_url,
        "audio": result.audio_url,
        "choices": result.choices
    }