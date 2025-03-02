from flask import Blueprint, request, jsonify
from models.image_generator import generate_image

image_bp = Blueprint('image_bp', __name__)

@image_bp.route("/generate-image", methods=["POST"])
def generate_image_route():
    data = request.json
    keywords = data.get("keywords", [])

    if not keywords:
        return jsonify({"error": "缺少关键词"}), 400

    try:
        image_url = generate_image(keywords)
        return jsonify({"image_url": image_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
