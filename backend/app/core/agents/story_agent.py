import openai
import os
from jinja2 import Template
import json
from langchain import Chain, Task
from app.core.memory.session_manager import get_story_state, add_story_state, get_conversation_memory

openai.api_key = os.getenv("OPENAI_API_KEY")

# 加载提示词模板
with open("app/utils/prompts/story_gen.jinja2", "r") as file:
    PROMPT_TEMPLATE = Template(file.read())

def process_user_input(user_id, user_input):
    # 获取用户的对话历史和当前故事状态
    conversation_history = get_conversation_memory(user_id)
    current_state = get_story_state(user_id) or "Once upon a time..."

    # 将对话历史和当前故事状态包含在提示词中
    prompt = PROMPT_TEMPLATE.render(
        user_input=user_input,
        conversation_history=conversation_history,
        current_state=current_state
    )
    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=500
    )
    return response.choices[0].text

# 加载生成故事的提示词模板
with open("app/utils/prompts/generate_story.jinja2", "r") as file:
    STORY_PROMPT_TEMPLATE = Template(file.read())

def generate_story(user_id, character_name, character_source, difficulty_level=5):
    # 获取用户的对话历史和当前故事状态
    conversation_history = get_conversation_memory(user_id)
    current_state = get_story_state(user_id) or "Once upon a time..."

    # 将对话历史和当前故事状态包含在提示词中
    prompt = STORY_PROMPT_TEMPLATE.render(
        difficulty_level=difficulty_level,
        character_name=character_name,
        character_source=character_source,
        current_state=current_state,
        conversation_history=conversation_history
    )
    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=500
    )
    story_data = json.loads(response.choices[0].text)
    add_story_state(user_id, story_data["story_text"])
    return story_data

def generate_image_task(story_text, character_image_path):
    from app.core.rendering.image_controller import generate_image
    return generate_image(story_text, character_image_path)

def generate_tts_task(response_text):
    from app.core.rendering.tts_controller import generate_tts
    return generate_tts(response_text, voice="female_child")

# 使用 LangChain 进行任务管理
def process_with_langchain(user_id, user_input):
    chain = Chain()

    # 第一个任务：处理用户输入
    process_user_input_task = Task(process_user_input, user_id, user_input)
    chain.add_task(process_user_input_task)

    # 条件判断：根据第一个任务的结果决定是否执行生成故事任务
    def condition_generate_story(result):
        response_json = json.loads(result)
        return response_json["marker"] == "[STORY]"

    generate_story_task = Task(generate_story, user_id, "Cinderella", "Disney")
    chain.add_task(generate_story_task, condition=condition_generate_story)

    # 生成图片任务
    character_image_path = "/path/to/character/images/cinderella.png"  # 角色图片路径
    generate_image_task = Task(generate_image_task, "{{story_text}}", character_image_path)
    chain.add_task(generate_image_task, condition=condition_generate_story)

    # 生成 TTS 任务
    generate_tts_task = Task(generate_tts_task, "{{response_text}}")
    chain.add_task(generate_tts_task)

    result = chain.run()
    return result
