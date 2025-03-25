from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class GuardrailCapability(str, Enum):
    VALIDATE = "validate"
    TRANSFORM = "transform"

@dataclass
class ValidationResult:
    passed: bool
    violations: List[str]

@dataclass
class TransformationResult:
    transformed_content: str
    details: Dict[str, Any]

class Guardrail(ABC):
    def __init__(self, id: str, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description
        self._capabilities = set()
        self._options = {}

    @property
    def capabilities(self) -> List[GuardrailCapability]:
        return list(self._capabilities)

    @property
    def options(self) -> Dict[str, Any]:
        return self._options

    def supports_capability(self, capability: GuardrailCapability) -> bool:
        return capability in self._capabilities

    def validate(self, content: str, options: Optional[Dict[str, Any]] = None) -> ValidationResult:
        if not self.supports_capability(GuardrailCapability.VALIDATE):
            raise NotImplementedError(f"Guardrail {self.id} does not support validation")
        return self._validate(content, options or {})

    def transform(self, content: str, options: Optional[Dict[str, Any]] = None) -> TransformationResult:
        if not self.supports_capability(GuardrailCapability.TRANSFORM):
            raise NotImplementedError(f"Guardrail {self.id} does not support transformation")
        return self._transform(content, options or {})

    @abstractmethod
    def _validate(self, content: str, options: Dict[str, Any]) -> ValidationResult:
        pass

    @abstractmethod
    def _transform(self, content: str, options: Dict[str, Any]) -> TransformationResult:
        pass

class GuardrailRegistry:
    _instance = None
    _guardrails: Dict[str, Guardrail] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GuardrailRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, guardrail: Guardrail):
        self._guardrails[guardrail.id] = guardrail

    def get(self, guardrail_id: str) -> Optional[Guardrail]:
        return self._guardrails.get(guardrail_id)

    def list_all(self) -> List[Dict[str, Any]]:
        """
        List all registered guardrails with their details.
        
        Returns:
            List of dictionaries containing guardrail information:
            - id: Unique identifier for the guardrail
            - name: Display name of the guardrail
            - description: Detailed description of what the guardrail does
            - supports_validation: Whether the guardrail supports validation
            - supports_transformation: Whether the guardrail supports transformation
            - options_schema: Schema of the options supported by the guardrail
              (includes type information, constraints, and examples)
        """
        return [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "supports_validation": g.supports_capability(GuardrailCapability.VALIDATE),
                "supports_transformation": g.supports_capability(GuardrailCapability.TRANSFORM),
                "options_schema": self._get_options_schema(g)
            }
            for g in self._guardrails.values()
        ]
        
    def _get_options_schema(self, guardrail: Guardrail) -> Dict[str, Any]:
        """
        Extract the options schema from a guardrail's options object if it's a Pydantic model.
        Otherwise, return the default options.
        """
        options = guardrail.options
        
        # Check if options is a Pydantic model instance by checking for common Pydantic model methods
        if hasattr(options, "__pydantic_fields__") or hasattr(options, "__fields__") or hasattr(options, "model_fields"):
            # Try to get schema based on Pydantic version
            schema = None
            if hasattr(options, "model_json_schema"):  # Pydantic v2
                schema = options.model_json_schema()
            elif hasattr(options, "schema"):  # Pydantic v1
                schema = options.schema()
            
            if schema:
                # Clean up schema to make it more user-friendly
                properties = schema.get("properties", {})
                required = schema.get("required", [])
                
                result = {}
                for field_name, field_schema in properties.items():
                    field_info = {
                        "type": field_schema.get("type", "any"),
                        "description": field_schema.get("description", ""),
                        "required": field_name in required
                    }
                    
                    # Mark required fields
                    if field_name in required:
                        field_info["required"] = True
                    
                    # Handle array types
                    if field_schema.get("type") == "array" and "items" in field_schema:
                        field_info["items"] = field_schema["items"]
                    
                    # Add constraints if they exist
                    for constraint in ["minimum", "maximum", "minLength", "maxLength", "pattern", "enum"]:
                        if constraint in field_schema:
                            field_info[constraint] = field_schema[constraint]
                    
                    # Include example values
                    if "default" in field_schema:
                        field_info["default"] = field_schema["default"]
                    elif hasattr(options, field_name):
                        # Use actual value as example
                        example_value = getattr(options, field_name)
                        # If it's a complex object, make sure it's serializable
                        if hasattr(example_value, "model_dump"):
                            example_value = example_value.model_dump()
                        elif hasattr(example_value, "dict"):
                            example_value = example_value.dict()
                        field_info["example"] = example_value
                    
                    result[field_name] = field_info
                
                return result
        
        # Fallback to returning the default options
        return options 