from flask import Flask
from app.routes.chat import chat_bp
from app.routes.story import story_bp
from app.routes.image import image_bp
from app.routes.tts import tts_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(story_bp, url_prefix='/story')
    app.register_blueprint(image_bp, url_prefix='/image')
    app.register_blueprint(tts_bp, url_prefix='/tts')

    return app
