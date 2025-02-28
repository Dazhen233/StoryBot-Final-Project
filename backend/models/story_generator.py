import openai

def generate_story(keywords, context):
    story_prompt = f"请用这些关键词编写一个有趣的儿童故事：{', '.join(keywords)}，并接着之前的故事：{context}"
    response = openai.Completion.create(
        engine="gpt-4",
        prompt=story_prompt,
        max_tokens=200
    )
    return response.choices[0].text.strip()
