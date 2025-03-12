import os
from PIL import Image
import io
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()
stability_api_key = os.getenv("STABILITY_API_KEY")
stability_api_host = os.getenv("STABILITY_API_HOST")

stability_api = client.StabilityInference(
    key=stability_api_key,
    verbose=True,
    engine="stable-diffusion-xl-1024-v1-0",
    host=stability_api_host
)

def generate_image(story_text, character_image_path):
    prompt = f"Generate an image based on the following story: {story_text} and include the character image: {character_image_path}"
    with open(character_image_path, "rb") as image_file:
        init_image = Image.open(io.BytesIO(image_file.read()))  # 转换为 PIL.Image
    
    answers = stability_api.generate(
        prompt=prompt,
        init_image=init_image,
        steps=50,
        cfg_scale=7.0,
        width=1920,
        height=1080,
        samples=1,
        sampler=generation.SAMPLER_K_DPMPP_2M
    )

    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                raise Exception("Your request activated the API's safety filters and could not be processed. Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                image_url = f"static/{artifact.seed}.png"
                with open(image_url, "wb") as f:
                    f.write(artifact.binary)
                print(f"Generated Image URL: /static/{artifact.seed}.png")    
                return f"/static/{artifact.seed}.png"
