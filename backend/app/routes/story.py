from flask import Blueprint, request, jsonify
from app.services.langchain_services import generate_story

story_bp = Blueprint('story', __name__)

@story_bp.route("/generate", methods=["POST"])
def generate():
    data = request.json
    keywords = data.get("keywords", [])
    context = data.get("context", "")

    if not keywords:
        return jsonify({"error": "缺少关键词"}), 400

    story = generate_story(keywords, context)
    return jsonify({"story": story})
