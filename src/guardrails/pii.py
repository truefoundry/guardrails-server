from typing import Dict, Any, List
from src.guardrails.base import Guardrail, GuardrailCapability, ValidationResult, TransformationResult
from src.models.presidio_model import PresidioModel
import re
from pydantic import BaseModel, field_validator, ValidationError, validator, Field

from src.guardrails.pii_types import PII_ENTITY_TYPE_MAP

class Options(BaseModel):
    """Options for the PII Guardrail."""
    entity_types: List[str] = Field(
        default=[],
        description="List of PII entity types to detect. One or more of: " + ", ".join(PII_ENTITY_TYPE_MAP.keys())
    )

    custom_regexes: List[Dict[str, str]] = Field(
        default=[],
        description="List of custom regex patterns to detect additional PII types. Each item should be a dictionary with 'pattern' (regex string) and 'label' (descriptive name)."
    )

    @field_validator('entity_types')
    def validate_entity_types(cls, v):
        for entity_type in v:
            if entity_type not in PII_ENTITY_TYPE_MAP.keys():
                raise ValueError(f"Invalid entity type: {entity_type}")
        return v

    @field_validator('custom_regexes')
    def validate_custom_regexes(cls, v):
        for regex in v:
            if 'pattern' not in regex or 'label' not in regex:
                raise ValueError("Each custom regex must have 'pattern' and 'label' keys.")
            try:
                re.compile(regex['pattern'])
            except re.error:
                raise ValueError(f"Invalid regex pattern: {regex['pattern']}")
        return v

class PIIGuardrail(Guardrail):
    def __init__(self):
        super().__init__(
            id="pii",
            name="PII Detection",
            description="Detects and handles personally identifiable information"
        )
        self._capabilities.add(GuardrailCapability.VALIDATE)
        self._capabilities.add(GuardrailCapability.TRANSFORM)
        self._options = Options(
            entity_types=[],
            custom_regexes=[]
        )
        self.model = PresidioModel()

    def _process_regex_patterns(self, text: str, custom_regexes: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Process text with custom regex patterns.
        
        Args:
            text: Input text to process
            custom_regexes: List of dictionaries containing regex patterns and their labels
            
        Returns:
            List of detected entities
        """
        entities = []
        for regex_config in custom_regexes:
            pattern = regex_config["pattern"]
            label = regex_config["label"]
            
            try:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entities.append({
                        "text": match.group(),
                        "label": f"CUSTOM_{label}",
                        "start": match.start(),
                        "end": match.end()
                    })
            except re.error:
                print(f"Invalid regex pattern: {pattern}")
                continue
                
        return entities

    def _validate(self, content: str, options: Dict[str, Any]) -> ValidationResult:
        # Override default options with any provided in context
        try:
            merged_options = self._options.model_copy(update=options)
            Options.model_validate(merged_options.model_dump())
        except ValidationError as e:
            raise Exception(f"Error in PII Guardrail: {str(e)}")
        
        # Get model-based detections
        _, model_entities = self.model.process_text(content, merged_options.model_dump())
        
        # Get regex-based detections
        custom_regexes = merged_options.custom_regexes
        regex_entities = self._process_regex_patterns(content, custom_regexes)
        
        # Combine all detected entities
        all_entities = model_entities + regex_entities
        
        # If any PII is found, validation fails
        violations = [
            f"Found {entity['label']} PII: {entity['text']}"
            for entity in all_entities
        ]
        
        return ValidationResult(
            passed=len(violations) == 0,
            violations=violations,
        )

    def _transform(self, content: str, options: Dict[str, Any]) -> TransformationResult:
        # Merge default options with provided options
        try:
            merged_options = self._options.model_copy(update=options)
            Options.model_validate(merged_options.model_dump())
        except ValidationError as e:
            raise Exception(f"Error in PII Guardrail: {str(e)}")
        
        
        # Get model-based detections and transformed text
        processed_text, model_entities = self.model.process_text(content, merged_options.model_dump())
        
        # Get regex-based detections
        custom_regexes = merged_options.custom_regexes
        regex_entities = self._process_regex_patterns(processed_text, custom_regexes)
        
        # Apply regex transformations
        if regex_entities:
            # Sort entities by start position in reverse order to avoid offset issues
            regex_entities.sort(key=lambda x: x["start"], reverse=True)
            
            # Convert processed_text back to mutable string
            processed_text = list(processed_text)
            
            # Replace each regex match with [PII]
            for entity in regex_entities:
                start, end = entity["start"], entity["end"]
                processed_text[start:end] = "[PII]"
            
            # Convert back to string
            processed_text = "".join(processed_text)
        
        # Combine all detected entities
        all_entities = model_entities + regex_entities
        
        return TransformationResult(
            transformed_content=processed_text,
            details={
                "entities": [
                    {
                        "type": entity["label"],
                        "original_text": entity["text"]
                    }
                    for entity in all_entities
                ],
                "applied_options": merged_options.model_dump()
            }
        ) 