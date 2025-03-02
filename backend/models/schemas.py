# models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

# ======================
# 基础模型
# ======================
class UserBase(BaseModel):
    username: str
    email: str

# ======================
# 请求模型
# ======================
class StoryCreate(BaseModel):
    """创建故事请求参数"""
    character: str
    theme: str
    difficulty_level: int = 1

    class Config:
        json_schema_extra = {
            "example": {
                "character": "elsa",
                "theme": "snow_adventure",
                "difficulty_level": 2
            }
        }

# ======================
# 响应模型 
# ======================
class StorySegment(BaseModel):
    """故事段落响应"""
    text: str
    image_url: str
    audio_url: str
    choices: List[str]

    class Config:
        orm_mode = True  # 允许从ORM对象转换

# ======================
# 数据库关系模型
# ======================
class UserWithStories(UserBase):
    """包含故事数据的用户响应"""
    stories: List[StorySegment] = []

    class Config:
        orm_mode = True