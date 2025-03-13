import os
import json
from jinja2 import Template
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
from langchain.memory import ConversationBufferMemory
from app.core.memory.session_manager import (
    get_story_state, add_story_state, 
    get_conversation_memory, add_conversation_memory, 
    get_user_character, update_user_character
)
from app.core.rendering.image_controller import generate_image
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 读取 OpenAI API 密钥
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("请设置环境变量 OPENAI_API_KEY，否则无法调用 OpenAI API！")

# 初始化 OpenAI LLM
llm = OpenAI(api_key=api_key)

# 读取对话模板
with open("app/utils/prompts/dialog.jinja2", "r", encoding="utf-8") as file:
    PROMPT_TEMPLATE = Template(file.read())

# 读取故事生成模板
with open("app/utils/prompts/generate_story.jinja2", "r", encoding="utf-8") as file:
    STORY_PROMPT_TEMPLATE = Template(file.read())

# 初始化 LangChain 内存
conversation_memory = ConversationBufferMemory(memory_key="conversation_history")


def process_user_input(user_id, user_input):
    """处理用户输入，并从 LLM 生成响应"""
    conversation_history = get_conversation_memory(user_id)
    #current_state = get_story_state(user_id) or "Once upon a time..."

    # 渲染 Jinja2 提示词模板
    prompt = PROMPT_TEMPLATE.render(
        user_input=user_input,
        conversation_history=conversation_history,
        #current_state=current_state
    )
    # 创建 LangChain PromptTemplate
    #prompt_template = PromptTemplate(
    #    input_variables=["user_input", "conversation_history"],# "current_state"], 
    #    template=prompt
    #)
    # 使用 `|` 代替 LLMChain
    #chain = prompt_template | llm
    #response = chain.invoke(#{
    #    "user_input": user_input,
    #    "conversation_history": conversation_history,
        #"current_state": current_state
    #}
    #)
    response = llm.invoke(prompt)
    #print("LLM Info:", llm)

    if response is None:
        print("\n⚠️ Warning: LLM returned None!\n")
    elif isinstance(response, str) and response.strip() == "":
        print("\n⚠️ Warning: LLM returned an empty string!\n")
    else:
        print("response:======>", response)

    # 解析 JSON 响应
    try:
        # 尝试将字符串转换为 JSON（Python 字典）
        response_json = json.loads(response)
        print("response JSON 转换成功！")
    except json.JSONDecodeError as e:
        # 如果转换失败，捕获异常并打印错误信息
        print("JSON 转换失败！")
        print(f"错误信息：{e}")
        response_json = json.loads(json.dumps({
        'intent': 'user_dialogue', 
        'reply': 'I am sorry, I am not able to understand you. do you like Cinderella?'
        }))
    intent = response_json.get("intent")
    character = response_json.get("character")
    next_action = response_json.get("next_action")
    reply = response_json.get("reply")
    
    # 记录对话历史
    add_conversation_memory(user_id, user_input, json.dumps(response_json))

    return intent, character, next_action, reply


def generate_story(user_id, user_input, character_name, difficulty_level=3):
    """生成故事"""
    conversation_history = get_conversation_memory(user_id)
    current_state = get_story_state(user_id) or "Once upon a time..."

    # 渲染 Jinja2 提示词模板
    prompt = STORY_PROMPT_TEMPLATE.render(
        difficulty_level=difficulty_level,
        character_name=character_name,
        current_state=current_state,
        last_question_answer=user_input
    )

    # 创建 PromptTemplate
    #prompt_template = PromptTemplate(
    #    input_variables=["difficulty_level", "character_name", "character_source", "current_state", "conversation_history"], 
    #    template=prompt
    #)

    # 使用 `|` 代替 LLMChain
    #chain = prompt_template | llm
    #response = chain.invoke({
    #    "difficulty_level": difficulty_level,
    #    "character_name": character_name,
    #    "character_source": character_source,
    #    "current_state": current_state,
    #    "conversation_history": conversation_history
    #})
    
    response = llm.invoke(prompt,max_tokens=1000)
    try:
        # 尝试将字符串转换为 JSON（Python 字典）
        response_json = json.loads(response)
        story_data = {'story_text': response_json.get("Story")+"-->"+response_json.get("Question")}
        print("story JSON 转换成功！")
    except json.JSONDecodeError as e:
        # 如果转换失败，捕获异常并打印错误信息
        print("story JSON 转换失败！")
        print(f"错误信息：{e}")
        story_data = {'story_text': response}

    add_story_state(user_id, "child reply:"+user_input+" "+response)
    return story_data


def generate_image_task(story_text, character_name):
    """生成故事对应的图片"""
    character_image_path = f"c:/Users/Steven/Downloads/StoryBot-Final-Project/backend/character_images/{character_name.lower()}.png"
    return generate_image(story_text, character_image_path)


def generate_tts_task(response_text):
    """生成故事的语音"""
    from app.core.rendering.tts_controller import generate_tts
    return generate_tts(response_text, voice="fable")


def process_with_langchain(user_id, user_input):
    """主逻辑：处理用户输入，执行对应任务"""
    intent, character, next_action, reply = process_user_input(user_id, user_input)
    print(f"Intent: ====> {intent}, Character: {character}, Next Action: {next_action}, reply :{reply}")

    if intent == "choose_character" or intent == "continue_story":
        # 更新用户选择的角色
        update_user_character(user_id, character)
        
        # 生成故事    user_input, character_name, difficulty_level=5
        story_data = generate_story(user_id, "", character)
        print(f"Story Text: {story_data['story_text']}")

        # 生成图片 & 语音
        story_data['image_url'] = generate_image_task(story_data["story_text"], character)
        story_data['audio_url'] = generate_tts_task(story_data["story_text"])

        return story_data
    elif intent == "continue_story":
        character_name = get_user_character(user_id) or "Cinderella"
        update_user_character(user_id, character_name)

        # 生成故事
        story_data = generate_story(user_id, user_input, character_name)
        print(f"Story Text: {story_data['story_text']}")

        # 生成图片 & 语音
        story_data['image_url'] = generate_image_task(story_data["story_text"],character_name)
        story_data['audio_url'] = generate_tts_task(story_data["story_text"])

        return story_data

    elif intent == "change_character":
        update_user_character(user_id, character)
        print(f"Change Character: {character}")
        story_data = generate_story(user_id, user_input, character)
        print(f"Story Text: {story_data['story_text']}")

        # 生成图片 & 语音
        story_data['image_url'] = generate_image_task(story_data["story_text"],character_name)
        story_data['audio_url'] = generate_tts_task(story_data["story_text"])

        return story_data
    elif intent == 'ask_question':
        story_data = {}
        story_data['story_text'] = reply
        story_data['audio_url'] = generate_tts_task(story_data["story_text"])
        return story_data
    else:   #"user_dialogue"
        story_data = {}
        story_data['story_text'] = reply
        story_data['audio_url'] = generate_tts_task(story_data["story_text"])
        return story_data

