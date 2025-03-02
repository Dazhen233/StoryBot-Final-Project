# core/rendering/tts_controller.py
import os
import logging
import base64
import hashlib
from typing import Optional, Dict
from pydantic import BaseModel
import openai
from app.config.settings import settings
from app.core.memory import SessionManager

logger = logging.getLogger("tts_controller")

# ======================
# 数据模型
# ======================
class TTSInput(BaseModel):
    text: str
    character: str  # 角色名称
    emotion: str = "neutral"  # 情感状态
    speed: float = 1.0  # 语速系数 (0.5-2.0)

class TTSOutput(BaseModel):
    audio_url: Optional[str]
    audio_data: Optional[bytes]
    duration: float  # 音频时长（秒）
    debug_info: dict

# ======================
# 语音控制器
# ======================
class TTSController:
    # 角色语音配置库
    VOICE_PROFILES = {
        "elsa": {
            "voice": "nova",
            "base_speed": 0.9,
            "pitch": 0.2,
            "style": "graceful"
        },
        "spongebob": {
            "voice": "echo",
            "base_speed": 1.2, 
            "pitch": 0.8,
            "style": "enthusiastic"
        },
        "thomas": {
            "voice": "fable",
            "base_speed": 1.0,
            "pitch": 0.5,
            "style": "cheerful"
        }
    }

    def __init__(self):
        self.cache = {}
        self.session_manager = SessionManager()

    async def text_to_speech(self, input: TTSInput) -> TTSOutput:
        """文本转语音主接口"""
        try:
            # 获取角色语音配置
            voice_config = self._get_voice_config(input.character)
            
            # 生成情感化文本
            processed_text = self._add_emotional_cues(input.text, input.emotion)
            
            # 计算缓存键
            cache_key = self._generate_cache_key(processed_text, voice_config)
            
            # 检查缓存
            if cached := self._check_cache(cache_key):
                return cached

            # 调用TTS API
            response = await openai.Audio.acreate(
                model="tts-1-hd",
                input=processed_text,
                voice=voice_config["voice"],
                speed=self._calculate_speed(voice_config["base_speed"], input.speed),
                response_format="mp3"
            )

            # 解析响应
            audio_data = response.content
            duration = self._estimate_duration(audio_data)
            
            # 更新缓存
            self._update_cache(cache_key, audio_data, duration)
            
            return TTSOutput(
                audio_data=audio_data,
                duration=duration,
                debug_info={
                    "character": input.character,
                    "model": "tts-1-hd",
                    "voice_config": voice_config,
                    "cache_hit": False
                }
            )

        except Exception as e:
            logger.error(f"TTS failed: {str(e)}")
            return self._generate_fallback(input.text)

    # ======================
    # 核心处理逻辑
    # ======================
    def _get_voice_config(self, character: str) -> Dict:
        """获取角色语音配置"""
        return self.VOICE_PROFILES.get(
            character.lower(), 
            {"voice": "nova", "base_speed": 1.0}
        )

    def _add_emotional_cues(self, text: str, emotion: str) -> str:
        """添加情感标记"""
        emotion_map = {
            "happy": "✨",
            "sad": "💧",
            "angry": "🔥",
            "surprised": "⚡"
        }
        return f"{emotion_map.get(emotion, '')} {text}"

    def _calculate_speed(self, base_speed: float, user_speed: float) -> float:
        """计算最终语速"""
        return max(0.5, min(2.0, base_speed * user_speed))

    def _generate_cache_key(self, text: str, config: Dict) -> str:
        """生成缓存键"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{config['voice']}_{text_hash}"

    def _estimate_duration(self, audio_data: bytes) -> float:
        """估算音频时长（简单实现）"""
        # 实际项目应使用音频解析库
        return len(audio_data) / 24000  # 近似估算

    # ======================
    # 缓存管理
    # ======================
    def _check_cache(self, key: str) -> Optional[TTSOutput]:
        """检查缓存"""
        if cached := self.cache.get(key):
            return TTSOutput(
                audio_data=cached["data"],
                duration=cached["duration"],
                debug_info={"cache_hit": True}
            )
        return None

    def _update_cache(self, key: str, data: bytes, duration: float):
        """更新缓存"""
        if len(self.cache) > 100:  # LRU缓存
            self.cache.popitem(last=False)
        self.cache[key] = {
            "data": data,
            "duration": duration
        }

    # ======================
    # 错误处理
    # ======================
    def _generate_fallback(self, text: str) -> TTSOutput:
        """生成备用响应"""
        return TTSOutput(
            audio_data=self._text_to_fallback_speech(text),
            duration=len(text)/5,  # 估算
            debug_info={"error": "使用备用语音生成"}
        )

    def _text_to_fallback_speech(self, text: str) -> bytes:
        """简单备用语音生成（可替换为本地TTS引擎）"""
        # 此处返回静默音频
        silent_mp3 = base64.b64decode("SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjMyLjEwNAAAAAAAAAAAAAAA//tQxAADB8AhSmxhIIEVFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVMQU1FMy45OS4yVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//sQBAAP8AAAaQAAAAgAAA0gAAABAAABpAAAACAAADSAAAAE")
        return silent_mp3

# ======================
# 使用示例
# ======================
async def example_usage():
    tts = TTSController()
    
    # 生成Elsa的语音
    elsa_audio = await tts.text_to_speech(TTSInput(
        text="Let's build a snow castle together!",
        character="elsa",
        emotion="happy"
    ))
    
    # 保存结果
    if elsa_audio.audio_data:
        with open("elsa_speech.mp3", "wb") as f:
            f.write(elsa_audio.audio_data)