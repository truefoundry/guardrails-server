from typing import Any, Dict, List

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, field_validator
from sentence_transformers import SentenceTransformer, util

from src.guardrails.base import (Guardrail, GuardrailCapability, TransformationResult,
                       ValidationResult)
from src.models.zero_shot_model import ZeroShotModel

load_dotenv()

class TopicOptions(BaseModel):
    denied_topics: List[str]
    threshold: float

    @field_validator('denied_topics')
    def validate_denied_topics(cls, v):
        if not v:
            raise ValueError("Denied topics list cannot be empty.")
        return v

    @field_validator('threshold')
    def validate_threshold(cls, v):
        if not (0 <= v <= 1):
            raise ValueError("Threshold must be between 0 and 1.")
        return v


class TopicGuardrail(Guardrail):
    def __init__(self):
        super().__init__(
            id="topics",
            name="Topic Control",
            description="Detects and blocks content related to denied topics"
        )
        self._capabilities.add(GuardrailCapability.VALIDATE)
        self._options = TopicOptions(
            denied_topics=[
                "Violence", 
                "Hate Speech",
                "Drugs",
                "Sexual Content"
            ],
            threshold=0.5  # Default threshold for topic detection
        )
        self.model = ZeroShotModel()

    def _validate(self, content: str, options: Dict[str, Any]) -> ValidationResult:
        # Merge default options with provided options
        try:
            merged_options = self._options.model_copy(update=options)
            TopicOptions.model_validate(merged_options.model_dump())
        except ValidationError as e:
            raise Exception(f"Error in Topic Guardrail: {str(e)}")
        
        denied_topics = merged_options.denied_topics
        threshold = merged_options.threshold
        
        # Detect denied topics
        detected_topics = self.model.detect_topics(content, denied_topics, threshold)
        
        # If any denied topic is detected, validation fails
        violations = [
            f"Content related to denied topic '{topic['topic']}'"
            for topic in detected_topics
        ]
        
        return ValidationResult(
            passed=len(violations) == 0,
            violations=violations,
        )
    def _transform(self, content: str, options: Dict[str, Any]) -> TransformationResult:
        raise NotImplementedError("Transformation is not supported by TopicGuardrail")