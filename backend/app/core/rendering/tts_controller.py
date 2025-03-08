import openai
import os
import uuid

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_tts(text, voice="female_child"):
    response = openai.Audio.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    audio_filename = f"{uuid.uuid4()}.mp3"
    audio_file_path = os.path.join("static", audio_filename)
    with open(audio_file_path, "wb") as f:
        f.write(response["audio"])
    return f"/static/{audio_filename}"
