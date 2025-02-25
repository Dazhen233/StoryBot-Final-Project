import React, { useState, useEffect, useRef } from 'react';
import './ChatbotUI.css';

export default function ChatbotUI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef(null);
  const [showInput, setShowInput] = useState(false);
  const [charging, setCharging] = useState(false);
  const [userInfoConfirmed, setUserInfoConfirmed] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState("en-US");

  const recognitionRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // **1. 处理发送消息**
  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    setMessages((prev) => [...prev, { text: userMessage, sender: "user" }]);
    setInput("");

    try {
        let endpoint = userInfoConfirmed ? "chat" : "start";

        const response = await fetch(`http://localhost:5000/${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: userMessage }),
        });

        const data = await response.json();

        if (data.error) {
            console.error("后端错误:", data.error);
            return;
        }

        if (data.reply) {
            setMessages((prev) => [...prev, { text: data.reply, sender: "bot" }]);
            setTimeout(() => {
                textToSpeech(data.reply, selectedVoice);
            }, 300);
        }

        if (data.keywords) {
            generateImage(data.keywords);
        }

        if (!userInfoConfirmed && data.reply.includes("Lets start the story")) {
            setUserInfoConfirmed(true);
        }
    } catch (error) {
        console.error("发送消息失败:", error);
    }
  };

  // **2. 解析关键词并生成图片**
  const generateImage = async (keywords) => {
    try {
        console.log("请求生成图片，关键词:", keywords);

        const response = await fetch("http://127.0.0.1:5000/generate-image", {  // 确保 URL 正确
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keywords }),
        });

        if (!response.ok) {
            throw new Error(`HTTP 错误！状态码: ${response.status}`);
        }

        const data = await response.json();
        console.log("图片 API 返回数据:", data);

        if (data.image_url) {
            setMessages((prev) => [...prev, { image: data.image_url, sender: "bot" }]);
        } else {
            console.error("API 没有返回图片 URL");
        }
    } catch (error) {
        console.error("图片生成失败:", error);
    }
};

  // **3. TTS 朗读机器人回复**
  const textToSpeech = async (text, voice) => {
    try {
        const response = await fetch("http://localhost:5000/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, voice }),
        });

        const data = await response.json();
        if (data.audio_url) {
            if (window.currentAudio) {
                window.currentAudio.pause();
            }
            const audio = new Audio(data.audio_url);
            window.currentAudio = audio;
            setTimeout(() => {
              console.log("开始播放音频");
              audio.play();
          }, 200);  // 延迟1秒播放音频
        } else {
            console.error("TTS API 未返回音频 URL");
        }
    } catch (error) {
        console.error("播放 TTS 失败:", error);
    }
  };

  // **4. 语音输入**
  const handleSpeechInput = () => {
    if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      alert("Your browser does not support Web Speech API. Please use Google Chrome!");
      return;
    }

    if (!isRecording) {
      setIsRecording(true);

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';  // 语音识别使用英文

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

  // **5. 解释单词拼写**
  const explainWords = async (word) => {
    try {
        const response = await fetch("http://localhost:5000/explain-word", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ word }),
        });

        const data = await response.json();
        if (data.definition && data.pronunciation) {
            setMessages((prev) => [...prev, { text: `${word}: ${data.definition} (发音: ${data.pronunciation})`, sender: "bot" }]);
            textToSpeech(`${word}, ${data.definition}`, "en-US");
        }
    } catch (error) {
        console.error("解释单词失败:", error);
    }
  };

  // **6. 处理欢迎消息并自动播放**
  const handleWelcomeClick = () => {
    setCharging(true);
    setTimeout(() => {
      setShowInput(true);
      setCharging(false);
      
      const welcomeMessage = "Hello, kid! Please introduce yourself. What's your name? How old are you? And what kind of stories do you like?";

      setMessages([{ text: welcomeMessage, sender: "bot" }]);

      // **自动播放欢迎语**
      textToSpeech(welcomeMessage, selectedVoice);
      
    }, 1500);
  };

  return (
    <div className="chat-container">
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
  
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender === 'user' ? 'user-message' : 'bot-message'}`}>
            {msg.text && <p>{msg.text}</p>}
            {msg.image && <img src={msg.image} alt="AI生成的图片" />}
          </div>
        ))}
        {isRecording && <div className="message bot-message">🎤 Listening...</div>}
        <div ref={messagesEndRef} />
      </div>
  
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
          <button onClick={handleSpeechInput} className={`mic-button ${isRecording ? 'recording' : ''}`}>
            {isRecording ? 'Recording...' : '🎤 语音'}
          </button>
        </div>
      )}
    </div>
  );
}

