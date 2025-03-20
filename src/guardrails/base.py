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
        return [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "supports_validation": g.supports_capability(GuardrailCapability.VALIDATE),
                "supports_transformation": g.supports_capability(GuardrailCapability.TRANSFORM),
                "options": g.options
            }
            for g in self._guardrails.values()
        ] 