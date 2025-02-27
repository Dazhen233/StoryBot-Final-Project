from flask import Blueprint, request, jsonify
from app.services.langchain_services import generate_story, extract_keywords, generate_image

chat_bp = Blueprint('chat', __name__)

chat_history = {}

@chat_bp.route("/start", methods=["POST"])
def start_chat():
    data = request.json
    user_id = "default"
    user_text = data.get("text", "")

    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append(user_text)

    bot_reply = generate_story([], "初始故事") 
    chat_history[user_id].append(bot_reply)

    return jsonify({"reply": bot_reply})

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = "default"
    user_text = data.get("text", "")

    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append(user_text)


    keywords = extract_keywords(user_text)


    context = " ".join(chat_history[user_id][-5:])
    bot_reply = generate_story(keywords, context)
    chat_history[user_id].append(bot_reply)

    image_url = generate_image(keywords)

    return jsonify({"reply": bot_reply, "keywords": keywords, "image_url": image_url})
