import openai
from flask import Blueprint, request, jsonify
import os

audio_blueprint = Blueprint('audio', __name__)

# 从环境变量中加载 OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_audio_openai(text: str, user_id: str):
    response = openai.Audio.create(
        model="text-to-speech",
        prompt=text,
        user_id=user_id
    )
    audio_url = response['data'][0]['url']
    return audio_url

@audio_blueprint.route('/generate', methods=['POST'])
def generate_audio():
    data = request.json
    text = data.get('text')
    user_id = data.get('user_id')  # 用来区分用户的ID
    if not text or not user_id:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    audio_url = generate_audio_openai(text, user_id)
    return jsonify({'audio_url': audio_url})
