class ImageRenderer:
    def __init__(self, strategy: str = "controlnet"):
        self.strategy = strategy
        self.impl = self._get_implementation()
    
    def _get_implementation(self):
        if self.strategy == "controlnet":
            return ControlNetRenderer()
        elif self.strategy == "lora":
            return LoRARenderer()
        else:
            raise ValueError("Unsupported rendering strategy")

    def render(self, prompt: str, pose_image: bytes) -> bytes:
        return self.impl.render(prompt, pose_image)