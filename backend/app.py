from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# **安全性改进：用环境变量存储 API Key**
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 存储用户对话上下文
chat_history = {}

# **1. 关键词提取**
def extract_keywords(text):
    try:
        prompt = f"请从以下文本中提取关键主题词，确保它们是单个词，并用逗号分隔：{text}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "你是一个关键词提取助手"},
                      {"role": "user", "content": prompt}]
        )
        return [kw.strip() for kw in response.choices[0].message.content.split(',')]
    except Exception as e:
        print("关键词提取失败:", str(e))
        return []

# **2. 生成 AI 故事**
def generate_story(keywords, context):
    try:
        story_prompt = f"请用这些关键词编写一个有趣的儿童故事：{', '.join(keywords)}，并接着之前的故事：{context}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "你是一个儿童故事讲述者"},
                      {"role": "user", "content": story_prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("故事生成失败:", str(e))
        return "我遇到了一点问题，稍后再试吧！"

# **3. AI 图片生成（DALL·E）**
@app.route("/generate-image", methods=["POST"])
def generate_image():
    data = request.json
    keywords = data.get("keywords", [])

    if not keywords:
        return jsonify({"error": "缺少关键词"}), 400

    try:
        image_prompt = f"一个动画风格的场景，包括 {', '.join(keywords)}"
        response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        return jsonify({"image_url": image_url})

    except Exception as e:
        print("图片生成失败:", str(e))
        return jsonify({"error": "图片生成失败"}), 500


# **4. 处理用户输入（对话）**
@app.route("/start", methods=["POST"])
def start_chat():
    data = request.json
    user_id = "default"
    user_text = data.get("text", "")

    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append(user_text)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "你是一个友好的儿童聊天机器人"},
                  {"role": "user", "content": user_text}]
    )

    bot_reply = response.choices[0].message.content
    chat_history[user_id].append(bot_reply)

    return jsonify({"reply": bot_reply})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = "default"
    user_text = data.get("text", "")

    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append(user_text)

    # **提取关键词**
    keywords = extract_keywords(user_text)

    # **生成故事**
    context = " ".join(chat_history[user_id][-5:])
    bot_reply = generate_story(keywords, context)
    chat_history[user_id].append(bot_reply)

    # **生成图片**
    image_url = generate_image(keywords)

    return jsonify({"reply": bot_reply, "keywords": keywords, "image_url": image_url})

# **5. 处理 TTS 朗读**
@app.route("/tts", methods=["POST"])
def text_to_speech():
    data = request.json
    text = data.get("text", "")

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )

        # **保存音频文件**
        audio_path = "tts_output.mp3"
        with open(audio_path, "wb") as audio_file:
            audio_file.write(response.content)

        return jsonify({"audio_url": f"http://127.0.0.1:5000/tts_output.mp3"})

    except Exception as e:
        print("TTS 生成失败:", str(e))
        return jsonify({"error": "无法生成语音"})

@app.route("/tts_output.mp3")
def get_tts_audio():
    return send_file("tts_output.mp3", mimetype="audio/mpeg")

# **6. 解释单词拼写**
@app.route("/explain-word", methods=["POST"])
def explain_word():
    data = request.json
    word = data.get("word", "")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "你是一个词典助手"},
                      {"role": "user", "content": f"请提供单词 {word} 的释义和拼音"}]
        )
        definition = response.choices[0].message.content

        return jsonify({"definition": definition, "pronunciation": f"{word} 的拼音"})
    except Exception as e:
        print("单词解释失败:", str(e))
        return jsonify({"error": "无法获取单词信息"})

if __name__ == '__main__':
    app.run(debug=True)
