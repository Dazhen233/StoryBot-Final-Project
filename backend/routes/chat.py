from flask import Blueprint, request, jsonify
from models.story_generator import generate_story
from models.image_generator import generate_image
from models.memory import update_memory, get_summary_memory
from audio import generate_audio

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route("/start", methods=["POST"])
def start_chat():
    data = request.json
    user_id = data.get("user_id")
    user_text = data.get("text")

    # 获取用户记忆（历史对话）
    context = get_summary_memory(user_id)

    # 生成故事
    keywords = user_text.split()  # 简单地从用户输入的文本提取关键词
    story = generate_story(keywords, context)
    
    # 生成图片
    image_url = generate_image(keywords)
    
    # 生成语音
    audio_url = generate_audio(story, user_id)

    # 更新记忆
    update_memory(user_id, user_text, story)

    return jsonify({"reply": story, "image_url": image_url, "audio_url": audio_url})

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get("user_id")
    user_text = data.get("text")

    # 获取用户记忆
    context = get_summary_memory(user_id)

    # 生成故事
    keywords = user_text.split()
    story = generate_story(keywords, context)
    
    # 生成图片
    image_url = generate_image(keywords)

    # 生成语音
    audio_url = generate_audio(story, user_id)

    # 更新记忆
    update_memory(user_id, user_text, story)

    return jsonify({"reply": story, "image_url": image_url, "audio_url": audio_url})
