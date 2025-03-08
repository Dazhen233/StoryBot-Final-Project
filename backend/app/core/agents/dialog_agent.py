import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

DIALOG_PROMPT_TEMPLATE = """
You are a children's English teaching assistant. Evaluate the following dialogue and provide feedback:

User input: "{user_input}"

Respond with appropriate feedback and encouragement.
"""

def evaluate_dialogue(user_input):
    prompt = DIALOG_PROMPT_TEMPLATE.format(user_input=user_input)
    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text
