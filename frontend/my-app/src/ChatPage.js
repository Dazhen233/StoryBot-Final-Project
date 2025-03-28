import React, { useState, useEffect, useRef} from "react";
import { useLocation } from "react-router-dom";
import './ChatPage.css';
import background from './assets/startPageBackground.jpg';
import fullBackground from './assets/fullBackground.jpg';
import speakButton from './assets/speakButton.png'; 
import listeningButton from './assets/listeningButton.png'; 



function ChatPage() {
  const location = useLocation();
  const [showButton, setShowButton] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [responseText, setResponseText] = useState("");  
  const [responseImage, setResponseImage] = useState(""); 
  const [responseAudio, setResponseAudio] = useState(""); 
  const recognitionRef = useRef(null);  // 语音识别对象
  
  const initialUserInput = useRef(location.state?.user_input || "Unknown");
  console.log("location.state:", location.state);

  const hasSentRequest = useRef(false);

  useEffect(() => {
    if (!hasSentRequest.current) {
      console.log("ChatPage 接收到的数据:", initialUserInput.current);
      sendToBackend(initialUserInput.current);
      hasSentRequest.current = true;  // 标记已经执行过
    }
  }, []);

  useEffect(() => {
    //2秒后显示按钮
    const timeout = setTimeout(() => setShowButton(true), 2000);
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (!("webkitSpeechRecognition" in window)) {
      console.warn("当前浏览器不支持 Web 语音识别 API");
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = "en-US"; // 语言英文
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = (event) => {
      console.error("语音识别错误:", event.error);
      setIsListening(false);
    };

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript; // 识别到的文本
      console.log("识别到文本:", text);
      sendToBackend(text); // 发送到后端
    };

    recognitionRef.current = recognition; // 存储 recognition 对象
  }, []);

   // 开始语音识别
  const startListening = () => {
    if (!recognitionRef.current) {
      alert("当前浏览器不支持语音识别，请使用 Chrome");
      return;
    }
    recognitionRef.current.start();
  };

  //发送文本到后端
  const sendToBackend = async (text) => {
    const requestBody = {
      user_id: "user123",  
      user_input: text     
    };
    
    try {
      console.log("即将发送到后端的文本:", requestBody);
      const response = await fetch("http://localhost:8000/story/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error("后端请求失败");
      } 
      console.log("文本成功发送到后端");

      const data = await response.json();
      console.log("后端返回的数据:", data);

      //setResponseText(data.text_response);  
      //setResponseImage(data.image_url);     
      //setResponseAudio(data.audio_url); 


    } catch (error) {
      console.error("请求失败:", error);
    }
  };

  return (
    <div className="fullPageBackground" style={{ backgroundImage: `url(${fullBackground})` }}>
      <div className="background" style={{ backgroundImage: `url(${background})` }}>

        {responseImage && <img src={responseImage} alt="Story Image" className="story-image" />}
        <img 
          src={isListening ? listeningButton : speakButton} 
          alt="speak"
          className="speakButton"
          onClick={startListening} // 传递函数
        />
      </div>
    </div>
  );

}

export default ChatPage;