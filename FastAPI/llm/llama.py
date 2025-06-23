import logger

import torch
from transformers import AutoTokenizer, AutoModelForCausalLm, pipeline

logging = logger.getLogger("logger")

class LocalLLMProcessor:
    def __init__(self,
                 model_path="Bllossom/llama-3.2-Korean-Bllossom-3B"):
        self.model_path = model_path
        self.tokenizer = None
        self.model = None
        self.load_model()

    def load_model(self):
        try:
            logger.info(f"모델 로딩 중 : {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLm.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_8bit=True
            )

        except Exception as e:
            logger.info(f"모델 로딩 오류 : {e}")


    def generate_response(self, prompt, max_length=512):
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        except Exception as e:
            logger.info(f"응답 생성 오류 : {e}")