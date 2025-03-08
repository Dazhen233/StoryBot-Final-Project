import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_image(keywords):
    prompt = f"Generate an image with the following keywords: {', '.join(keywords)}"
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1920x1080"
    )
    return response.data[0].url
