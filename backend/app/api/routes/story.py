from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.core.agents.story_agent import generate_story
from app.core.rendering.image_controller import generate_image
from app.core.rendering.tts_controller import generate_tts

router = APIRouter()

class StoryRequest(BaseModel):
    user_id: str
    character_name: str
    character_source: str
    current_state: str

@router.post("/generate")
async def generate_story_endpoint(request: StoryRequest, background_tasks: BackgroundTasks):
    try:
        story_data = generate_story(request.character_name, request.character_source, request.current_state)
        background_tasks.add_task(generate_image, story_data['keywords'])
        background_tasks.add_task(generate_tts, story_data['story_text'])
        return {"status": "processing", "story_data": story_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
