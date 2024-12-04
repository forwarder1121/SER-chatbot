import os
from dataclasses import dataclass
from typing import Dict
from transformers import pipeline
from openai import OpenAI

os.environ["TOKENIZERS_PARALLELISM"] = "false"

@dataclass
class ChatbotService:
    def __init__(self, openai_config):
        self.client = OpenAI(api_key=openai_config.api_key)
        self.emotion_classifier = pipeline(
            "text-classification", 
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,
            device=-1
        )

    def analyze_emotion(self, text: str) -> Dict[str, float]:
        results = self.emotion_classifier(text)
        return {score['label']: score['score'] for score in results[0]}

    def get_response(self, user_input: str) -> str:
        emotions = self.analyze_emotion(user_input)
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
        
        messages = [
            {"role": "system", "content": f"사용자의 감정: {dominant_emotion}"},
            {"role": "user", "content": user_input}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content
