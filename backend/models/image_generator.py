import openai


openai=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


CHARACTER_TEMPLATES = {
    "snow_white": "https://your-server.com/images/snow_white_template.png",
    "twilight_sparkle": "https://your-server.com/images/twilight_sparkle_template.png",
    "cinderella": "https://your-server.com/images/cinderella_template.png"
}

def generate_image(keywords):
    # 从关键词中提取角色名称
    character = keywords[0] if keywords else None
    
    if not character or character not in CHARACTER_TEMPLATES:
        raise ValueError("角色未找到或无效")
    
    # 获取该角色的参考模板图像链接
    template_url = CHARACTER_TEMPLATES.get(character)
    
    try:
        response = openai.Image.create(
            prompt=f"Generate a new image in the style of this character, based on the reference image: {template_url}",
            n=1,
            size="1024x1024"
        )
        
        image_url = response['data'][0]['url']
        return image_url
    
    except Exception as e:
        raise Exception(f"生成图像失败: {str(e)}")
