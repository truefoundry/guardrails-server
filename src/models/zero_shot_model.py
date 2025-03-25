import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from transformers import pipeline

load_dotenv()


class ZeroShotModel:
    """
    A model for zero-shot topic classification using Hugging Face transformers.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv("ZERO_SHOT_MODEL_NAME")
        self.model = None
        self.load_model()

    def load_model(self):
        """
        Load the zero-shot-classification model from Hugging Face.
        """
        try:
            self.model = pipeline("zero-shot-classification", model=self.model_name, device=0)
            print(f"Model loaded successfully: {self.model_name}")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise

    def is_model_loaded(self) -> bool:
        """
        Check if the model is loaded successfully.
        """
        return self.model is not None

    def detect_topics(self, text: str, denied_topics: List[str], threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Detect if text relates to any of the denied topics.
        
        Args:
            text: Input text to process
            denied_topics: List of denied topics to check against
            threshold: Threshold value for topic relevance (0-1)
            
        Returns:
            List of detected topics with their scores
        """
        if not self.is_model_loaded():
            raise Exception("Model not loaded")

        detected_topics = []
        for topic in denied_topics:
            result = self.model(text, [topic])
            label = result['labels'][0]
            score = result['scores'][0]
            if label == topic and score >= threshold:
                detected_topics.append({
                    "topic": topic,
                    "score": score
                })

        return detected_topics 