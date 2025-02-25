import React, { useState, useEffect, useRef } from 'react';
import './ChatbotUI.css';

export default function ChatbotUI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false); // 录音状态
  const messagesEndRef = useRef(null);
  const [showInput, setShowInput] = useState(false);
  const [charging, setCharging] = useState(false);

  // 存储用户输入信息
  const [userInfo, setUserInfo] = useState({ name: "", age: "", gender: "" });
  const [infoFinalized, setInfoFinalized] = useState(false); //  数据是否锁定
  const [waitingForChange, setWaitingForChange] = useState(null); //  记录正在修改哪个字段

  // 机器人提问相关
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const questions = [
    "Hi, Please tell me your name.",
    "How old are you？",
    "Are you a boy or a girl."
  ];

  // 语音录制相关状态
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    if (showInput && messages.length === 0) {
      setMessages([{ text: questions[currentQuestion], sender: 'bot' }]);
    }
  }, [showInput]);

  const handleWelcomeClick = () => {
    setCharging(true);
    setTimeout(() => {
      setShowInput(true);
      setCharging(false);
      setMessages([{ text: questions[currentQuestion], sender: 'bot' }]); // 机器人开始提问
    }, 1500);
  };

  // 处理用户消息发送
  const handleSend = async () => {
    if (input.trim() !== '') {
        const userMessage = input.toLowerCase();
        setMessages(prevMessages => [...prevMessages, { text: userMessage, sender: 'user' }]);
        setInput('');

        // 处理修改用户信息的指令
        if (userMessage.includes("change name")) {
            setWaitingForChange("name");
            setMessages(prevMessages => [...prevMessages, { text: "Okay! What's your new name?", sender: 'bot' }]);
            return;
        } else if (userMessage.includes("change age")) {
            setWaitingForChange("age");
            setMessages(prevMessages => [...prevMessages, { text: "Alright! How old are you?", sender: 'bot' }]);
            return;
        } else if (userMessage.includes("change gender")) {
            setWaitingForChange("gender");
            setMessages(prevMessages => [...prevMessages, { text: "Got it! Are you a boy or a girl?", sender: 'bot' }]);
            return;
        }

        // 如果用户正在修改信息，则保存新输入并更新数据
        if (waitingForChange) {
            const updatedUserInfo = { ...userInfo, [waitingForChange]: userMessage };
            setUserInfo(updatedUserInfo);
            setWaitingForChange(null);

            const response = await saveUserData(updatedUserInfo);
            if (response && response.reply) {
                setMessages(prevMessages => [...prevMessages, { text: response.reply, sender: 'bot' }]);
            } else {
                setMessages(prevMessages => [...prevMessages, { text: "Error updating info!", sender: 'bot' }]);
            }
            return;
        }

        // 处理常规的问答流程
        if (!infoFinalized) {
            let updatedUserInfo = { ...userInfo };

            if (currentQuestion === 0) {
                updatedUserInfo.name = userMessage;
            } else if (currentQuestion === 1) {
                updatedUserInfo.age = userMessage;
            } else if (currentQuestion === 2) {
                updatedUserInfo.gender = userMessage;
                setInfoFinalized(true);
            }

            setUserInfo(updatedUserInfo);
            const response = await saveUserData(updatedUserInfo);
            if (response && response.reply) {
                setMessages(prevMessages => [...prevMessages, { text: response.reply, sender: 'bot' }]);
            } else {
                setMessages(prevMessages => [...prevMessages, { text: "Failed to save user info!", sender: 'bot' }]);
            }
        }
        // 继续提问
        if (currentQuestion < questions.length - 1) {
            setTimeout(() => {
                setMessages(prevMessages => [...prevMessages, { text: questions[currentQuestion + 1], sender: 'bot' }]);
                setCurrentQuestion(prev => prev + 1);
            }, 1000);
        }
    }
};

//  发送数据到后端
const saveUserData = async (userData) => {
  try {
    const response = await fetch('http://localhost:5000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });

    if (!response.ok) {
      throw new Error(`HTTP 错误！状态码: ${response.status}`);
    }

    const result = await response.json(); // 解析后端返回的 JSON 数据
    console.log('后端返回的数据:', result);
    return result; // 确保返回数据，供前端使用
  } catch (error) {
    console.error('Error:', error);
    return null; // 返回 null，防止出错
  }
};

// 处理语音输入
const recognitionRef = useRef(null);

const handleSpeechInput = () => {
  if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
    alert("你的浏览器不支持 Web Speech API，请使用 Google Chrome！");
    return;
  }

  if (!isRecording) {
    setIsRecording(true);

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let transcript = event.results[event.results.length - 1][0].transcript;
      setInput(transcript);

      if (event.results[event.results.length - 1].isFinal) {
        setInput(transcript.trim());
      }
    };

    recognition.onend = () => {
      setIsRecording(false);
      recognitionRef.current = null;
    };

    recognition.start();
    recognitionRef.current = recognition;
  } else {
    setIsRecording(false);
    recognitionRef.current?.stop();
  }
};

//自动滚动聊天窗口到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-container">
      {/* 欢迎界面 */}
      {!showInput && messages.length === 0 && (
        <div className="welcome-container">
          <div className="click-here-bubble moving-bubble">Click Here!</div>
          <div 
            className={`welcome-message ${charging ? 'charging' : ''}`} 
            onClick={handleWelcomeClick}
          >
            Hi, Click here to start a chat!
          </div>
        </div>
      )}
  
      {/* 聊天消息框 */}
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender === 'user' ? 'user-message' : 'bot-message'}`}>
            {msg.text}
          </div>
        ))}
        {/* 显示 "Listening..." 提示，仅在录音时出现 */}
        {isRecording && (
          <div className="message bot-message">🎤 Listening...</div>
        )}
        <div ref={messagesEndRef} />
      </div>
  
      {/* 输入框 & 语音按钮 */}
      {showInput && (
        <div className="input-container">
          <input
            type="text"
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Input..." 
          />
          <button onClick={handleSend} className="send-button">Send</button>
          {/* 语音输入按钮 */}
          <button onClick={handleSpeechInput} className={`mic-button ${isRecording ? 'recording' : ''}`}>
            {isRecording ? 'Recording...' : '🎤 语音'}
          </button>
        </div>
      )}
    </div>
  );
}








/////////////////////////



from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import openai
import os

app = Flask(__name__)
CORS(app)

# 设置 OpenAI API Key
openai.api_key = "your_api_key"

# JSON 文件路径
user_data_file = "user_data.json"

# **启动 Flask 时清空数据**
if os.path.exists(user_data_file):
    with open(user_data_file, "w", encoding="utf-8") as file:
        json.dump({}, file)  # 存入一个空字典，确保文件格式正确

# 读取数据（如果文件不存在，返回空字典）
def load_data():
    try:
        with open(user_data_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# 覆盖写入数据
def save_data(data):
    with open(user_data_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': '未收到数据'}), 400

    print("收到的 JSON 数据:", data)

    # 读取当前存储的数据
    current_data = load_data()

    # **合并新数据**
    current_data.update(data)
    save_data(current_data)  # 存储更新后的数据

    # **检查是否所有信息都已填写且不为空**
    if all(key in current_data and current_data[key].strip() for key in ["name", "age", "gender"]):
        return jsonify({'reply': 'All data has been saved, Thank you!'})  # 所有信息已填充且不为空，返回最终消息
    else:
        return jsonify({'reply': 'save!'})  # 继续存储数据


@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

# 处理 TTS 请求
@app.route("/tts", methods=["POST"])
def tts():
    data = request.json
    text = data.get("text", "")
    voice = data.get("voice", "alloy")  # 可选 alloy, echo, fable, onyx, nova, shimmer

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        response = openai.Audio.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        audio_file = "output.mp3"
        with open(audio_file, "wb") as f:
            f.write(response["audio"])

        return send_file(audio_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)