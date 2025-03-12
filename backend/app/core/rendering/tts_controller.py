import openai
import os
import uuid
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_tts(text, voice="fable"):
    audio_filename = f"{uuid.uuid4()}.mp3"
    audio_file_path = os.path.join("static", audio_filename)

    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    # 保存音频到文件
    with open(audio_file_path, "wb") as f:
        f.write(response.content)

    print(f"Generated Audio URL: /static/{audio_filename}")
    return f"/static/{audio_filename}"
