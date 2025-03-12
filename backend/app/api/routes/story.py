from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.core.agents.story_agent import process_with_langchain
from app.core.memory.session_manager import get_all_conversation_memory
import json

router = APIRouter()

class UserRequest(BaseModel):
    user_id: str
    user_input: str

@router.post("/process")
async def process_request(request: UserRequest, background_tasks: BackgroundTasks):
    try:
        response_data = process_with_langchain(request.user_id, request.user_input)

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
async def get_conversations():
    try:
        conversations = get_all_conversation_memory()
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
