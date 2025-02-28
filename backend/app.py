from flask import Flask
from routes.audio import audio_blueprint
from routes.chat import story_blueprint
from routes.image import image_blueprint

app = Flask(__name__)

app.register_blueprint(audio_blueprint, url_prefix='/audio')
app.register_blueprint(story_blueprint, url_prefix='/story')
app.register_blueprint(image_blueprint, url_prefix='/image')

if __name__ == '__main__':
    app.run(debug=True)
