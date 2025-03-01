class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
    
    # 分层配置
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    stability: StabilitySettings = Field(default_factory=StabilitySettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)

class OpenAISettings(BaseSettings):
    api_key: str
    story_model: str = "gpt-4-1106-preview"
    tts_model: str = "tts-1-hd"

class StabilitySettings(BaseSettings):
    api_key: str 
    engine: str = "stable-diffusion-xl-1024-v1-0"
    controlnet: str = "openpose"