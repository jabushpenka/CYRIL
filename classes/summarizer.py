import openai
import logging

# переменные окружения
import os
from dotenv import load_dotenv
load_dotenv()

# чтоб мозги не компостировал
logging.getLogger("openai").setLevel(logging.WARNING)

class Summarizer:
    def __init__(self, model: str = "aliceai-llm-flash/latest"):
        """
        Инициализация клиента YandexGPT.
        
        :param api_key: API-ключ из AI Studio / Yandex Cloud
        :param folder_id: ID каталога (Folder ID)
        :param model: Название модели
        """
        self.folder_id = os.getenv("FOLDERID")
        self.model_uri = f"gpt://{self.folder_id}/{model}"

        self.client = openai.OpenAI(
            api_key=os.getenv("APIKEY"),
            base_url="https://ai.api.cloud.yandex.net/v1",
            project=os.getenv("FOLDERID")
        )

    def summarize_to_single_sentence(self, text_array: list) -> str:
        """
        Принимает массив строк и возвращает пересказ одним предложением.
        """
        if not text_array or not any(str(text).strip() for text in text_array):
            return "Входные данные пусты."

        combined_text = "\n".join(str(text).strip() for text in text_array)

        #Инструкция
        instructions = (
            "Ты профессиональный редактор. Сделай краткий пересказ текста "
            "РОВНО В ОДНОМ ПРЕДЛОЖЕНИИ на русском языке. "
            "Без списков, без нескольких предложений. "
            "Только одна законченная мысль с одной точкой в конце."
        )

        try:
            response = self.client.responses.create(
                model=self.model_uri,
                temperature=0.1,
                instructions=instructions,
                input=combined_text,
                max_output_tokens=300
            )
            
            summary = response.output_text.strip()
            
            #гарантия одного предложения
            if summary.count('.') > 1:
                summary = summary.split('.')[0] + '.'
                
            return summary

        except Exception as e:
            return f"Ошибка API: {e}"