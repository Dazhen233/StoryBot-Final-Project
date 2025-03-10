from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.core.agents.story_agent import process_with_langchain
import json

router = APIRouter()

class UserRequest(BaseModel):
    user_id: str
    user_input: str

@router.post("/process")
async def process_request(request: UserRequest, background_tasks: BackgroundTasks):
    try:
        response_data = process_with_langchain(request.user_id, request.user_input)
        response_json = json.loads(response_data)
        response_text = response_json["response_text"]
        marker = response_json["marker"]

        if marker == "[STORY]":
            return {
                "response": response_text,
                "audio_url": response_json["audio_url"],
                "image_url": response_json["image_url"]
            }
        else:
            return {"response": response_text, "audio_url": response_json["audio_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
