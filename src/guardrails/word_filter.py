from typing import Dict, Any, List
from pydantic import BaseModel, field_validator, ValidationError, Field
from src.guardrails.base import Guardrail, GuardrailCapability, ValidationResult, TransformationResult
import re

class WordFilterOptions(BaseModel):
    """Options for the Word Filter Guardrail."""
    word_list: List[str] = Field(
        default=[],
        description="List of words to filter out"
    )
    case_sensitive: bool = Field(
        default=False,
        description="Whether word matching should be case sensitive"
    )
    
    whole_words_only: bool = Field(
        default=True,
        description="Whether to match whole words only (not parts of words)"
    )
    
    replacement: str = Field(
        default="[FILTERED]",
        description="Text to replace filtered words with"
    )

class WordFilterGuardrail(Guardrail):
    def __init__(self):
        super().__init__(
            id="word",
            name="Word Filter",
            description="Filters and transforms content based on a list of words"
        )
        self._capabilities.add(GuardrailCapability.VALIDATE)
        self._capabilities.add(GuardrailCapability.TRANSFORM)
        self._options = WordFilterOptions(
            word_list=[],
            case_sensitive=False,
            whole_words_only=True,
            replacement="[FILTERED]"
        )

    def _create_word_pattern(self, word: str, whole_words_only: bool) -> str:
        """Create a regex pattern for word matching."""
        if whole_words_only:
            return r'\b' + re.escape(word) + r'\b'
        return re.escape(word)

    def _validate(self, content: str, options: Dict[str, Any]) -> ValidationResult:
        # Merge default options with provided options
        try:
            merged_options = self._options.model_copy(update=options)
            WordFilterOptions.model_validate(merged_options.model_dump())
        except ValidationError as e:
            raise Exception(f"Error in Word Filter Guardrail: {str(e)}")
        
        word_list = merged_options.word_list
        case_sensitive = merged_options.case_sensitive
        whole_words_only = merged_options.whole_words_only
        
        # Create regex pattern for all words
        flags = 0 if case_sensitive else re.IGNORECASE
        patterns = [self._create_word_pattern(word, whole_words_only) for word in word_list]
        combined_pattern = '|'.join(patterns)
        
        # Find all matches
        matches = re.finditer(combined_pattern, content, flags)
        
        # Collect violations
        violations = [
            f"Found filtered word: {match.group()}"
            for match in matches
        ]
        
        return ValidationResult(
            passed=len(violations) == 0,
            violations=violations,
        )

    def _transform(self, content: str, options: Dict[str, Any]) -> TransformationResult:
        # Merge default options with provided options
        try:
            merged_options = self._options.model_copy(update=options)
            WordFilterOptions.model_validate(merged_options.model_dump())
        except ValidationError as e:
            raise Exception(f"Error in Word Filter Guardrail: {str(e)}")
        
        word_list = merged_options.word_list
        case_sensitive = merged_options.case_sensitive
        whole_words_only = merged_options.whole_words_only
        replacement = merged_options.replacement
        
        # Create regex pattern for all words
        flags = 0 if case_sensitive else re.IGNORECASE
        patterns = [self._create_word_pattern(word, whole_words_only) for word in word_list]
        combined_pattern = '|'.join(patterns)
        
        # Replace all matches
        transformed_content = re.sub(
            combined_pattern,
            replacement,
            content,
            flags=flags
        )
        
        # Find all matches for details
        matches = re.finditer(combined_pattern, content, flags)
        filtered_words = [match.group() for match in matches]
        
        return TransformationResult(
            transformed_content=transformed_content,
            details={
                "filtered_words": filtered_words,
                "applied_options": merged_options.model_dump()
            }
        ) 