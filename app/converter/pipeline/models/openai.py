import os

import requests
from openai import OpenAI
import base64

from app.converter.stage.stage import Stage
from app.converter.utils.helpers import delete_latex_md

class AIExtractor(Stage):
    def __init__(self, api_key, proxies):
        key = os.path.expandvars(api_key)
        self.client = OpenAI(api_key=key, http_client=requests.Session().proxies.update(proxies))

    def get_name(self):
        return "result"

    def process(self, data):
        with open(data['img'], "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text",
                         "text": f"Конвертируй это в LaTeX-разметку, для вспомогательных данных можешь использовать данные, которые я получил из другой OCR: "
                                 f"найденный текст: {data['text']}, "
                                 f"найденные таблицы в формате JSON-строки: {" \n".join(data['tables'])}, "
                                 f"найденные формулы: {" \n".join(data['formulas'])}. Если есть какие-то ошибки или опечатки - исправь. ВЕРНИ ТОЛЬКО LaTeX-РАЗМЕТКУ!!!!"
                         },
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
        )

        return delete_latex_md(response.choices[0].message.content)
