import openai
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_story(text):
    try:
        prompt = f"请根据下列输入进行童话故事创作{text}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "你是一个英语教师，化身动画形象，教育孩子们英语"},
                      {"role": "user", "content": prompt}]
        )
        return [kw.strip() for kw in response.choices[0].message.content.split(',')]
    except Exception as e:
        print("故事生成失败:", str(e))
        return []


