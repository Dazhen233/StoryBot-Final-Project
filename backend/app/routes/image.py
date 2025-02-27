from flask import Blueprint, request, jsonify
from app.services.langchain_services import generate_image

image_bp = Blueprint('image', __name__)

@image_bp.route("/generate", methods=["POST"])
def generate():
    data = request.json
    keywords = data.get("keywords", [])

    if not keywords:
        return jsonify({"error": "缺少关键词"}), 400

    image_url = generate_image(keywords)

    if image_url:
        return jsonify({"image_url": image_url})
    else:
        return jsonify({"error": "图片生成失败"}), 500
