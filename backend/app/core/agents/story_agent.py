import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

STORY_PROMPT_TEMPLATE = """
You are a children's English teaching assistant. Generate a story that:

1. Contains exactly {difficulty_level} new vocabulary words from CEFR A1 list
2. Includes 3 interactive decision points marked with [CHOICE]
3. Use simple past tense and present continuous tense
4. Main character: {character_name} from {character_source}
5. Current story state: {current_state}

Respond in JSON format:
{
  "story_text": "...",
  "choices": ["...", "...", "..."],
  "target_vocab": ["...", "..."]
}
"""

def generate_story(character_name, character_source, current_state, difficulty_level=5):
    prompt = STORY_PROMPT_TEMPLATE.format(
        difficulty_level=difficulty_level,
        character_name=character_name,
        character_source=character_source,
        current_state=current_state
    )
    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=500
    )
    return response.choices[0].text
