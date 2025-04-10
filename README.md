# Guardrails Server

A robust service for implementing safety and quality controls on Large Language Model (LLM) outputs. This service provides multiple guardrails to ensure LLM responses are safe, appropriate, and meet specified quality standards.

## Features

- **Multiple Guardrail Types:**
  - Content Safety Filters (`safety`)
    - Violence detection (low/medium/high)
    - Hate speech detection (low/medium/high)
    - Insults detection (low/medium/high)
    - Misconduct detection (low/medium/high)
    - Sexual content detection (low/medium/high)
  - Topic Control (`topics`)
    - Denied topics list
  - Word Filtering (`words`)
    - Built-in profanity detection
    - Custom word list filtering
  - PII Detection and Protection (`pii`)
    - Standard PII types (email, phone, SSN, credit card, address, name, date of birth, IP address, passport, drivers license)
    - Custom regex patterns for additional entity detection

## API Endpoints

### 1. List Available Guardrails
```http
GET /api/v1/guardrails
```

Returns a list of all available guardrails and their capabilities.

**Response:**
```json
{
  "guardrails": [
    {
      "id": "pii",
      "name": "PII Detection",
      "description": "Detects and handles personally identifiable information",
      "supports_validation": true,
      "supports_transformation": true,
      "options": {
        "entity_types": [
          "email",
          "phone",
          "ssn",
          "credit_card",
          "address",
          "name",
          "date_of_birth",
          "ip_address",
          "passport",
          "drivers_license"
        ],
        "custom_regexes": [
          {
            "pattern": "regex_pattern",
            "label": "custom_entity_label"
          }
        ]
      }
    },
    {
      "id": "profanity",
      "name": "Profanity Filter",
      "description": "Detects and filters offensive language",
      "supports_validation": true,
      "supports_transformation": true,
      "options": {
        "severity_levels": ["mild", "moderate", "severe"]
      }
    }
  ]
}
```

### 2. Validate Response
```http
POST /api/v1/validate
```

Validates an LLM response against specified guardrails and returns whether it passes or fails. Supports both single string content and batch processing of multiple strings.

**Request Body:**
```json
{
  "content": "LLM response text" | ["LLM response text 1", "LLM response text 2"],
  "guardrails": ["pii", "profanity", "relevancy"],
  "options": {
    "pii": {
      "entity_types": ["email", "phone", "ssn"],
      "custom_regexes": [
        {
          "pattern": "\\b[A-Z0-9._%+-]+@example\\.com\\b",
          "label": "company_email"
        }
      ]
    },
    "profanity": {},
    "relevancy": {}
  }
}
```

**Response (Single String):**
```json
{
  "is_valid": boolean,
  "failed_guardrails": ["string"],
  "details": {
    "content_0": {
      "passed": boolean,
      "violations": ["string"],
      "guardrail_details": {
        "guardrail_id": {
          "passed": boolean,
          "violations": ["string"]
        }
      }
    }
  }
}
```

**Response (Multiple Strings):**
```json
{
  "is_valid": boolean,
  "failed_guardrails": ["string"],
  "details": {
    "content_0": {
      "passed": boolean,
      "violations": ["string"],
      "guardrail_details": {
        "guardrail_id": {
          "passed": boolean,
          "violations": ["string"]
        }
      }
    },
    "content_1": {
      "passed": boolean,
      "violations": ["string"],
      "guardrail_details": {
        "guardrail_id": {
          "passed": boolean,
          "violations": ["string"]
        }
      }
    }
  }
}
```

### 3. Transform Response
```http
POST /api/v1/transform
```

Applies specified transformations to make the content compliant with guardrails. Supports both single string content and batch processing of multiple strings.

**Request Body:**
```json
{
  "content": "LLM response text" | ["LLM response text 1", "LLM response text 2"],
  "guardrails": ["pii", "profanity"],
  "options": {
    "pii": {
      "entity_types": ["email", "phone", "ssn"],
      "custom_regexes": [
        {
          "pattern": "\\b[A-Z0-9._%+-]+@example\\.com\\b",
          "label": "company_email"
        }
      ]
    },
    "profanity": {}
  }
}
```

**Response (Single String):**
```json
{
  "transformed_content": "string",
  "applied_transformations": ["string"],
  "details": {
    "content_0": {
      "guardrail_id": {
        "details": {}
      }
    }
  }
}
```

**Response (Multiple Strings):**
```json
{
  "transformed_contents": ["string", "string"],
  "applied_transformations": ["string"],
  "details": {
    "content_0": {
      "guardrail_id": {
        "details": {}
      }
    },
    "content_1": {
      "guardrail_id": {
        "details": {}
      }
    }
  }
}
```

### 4. Health Check
```http
GET /health
```

Verifies the service is running and all guardrails are properly initialized.

**Response:**
```json
{
  "status": "healthy",
  "guardrails": {
    "pii": true,
    "profanity": true
  }
}
```

## Project Structure

The project is organized into the following structure:

```
guardrails-service/
├── config/              # Configuration files
│   └── .env             # Environment variables
├── src/                 # Source code
│   ├── api/             # API endpoints and application server
│   │   └── app.py       # FastAPI application
│   ├── guardrails/      # Guardrail implementations
│   │   ├── base.py      # Base guardrail classes and interfaces
│   │   ├── pii.py       # PII detection guardrail
│   │   ├── pii_types.py # PII entity types
│   │   └── topic.py     # Topic control guardrail
│   └── models/          # ML model services
│       └── service.py   # Model service implementations
├── .env                 # Environment variables (root copy for compatibility)
├── Dockerfile           # Container definition
├── requirements.txt     # Python dependencies
└── run.py               # Entry point script
```

## Getting Started

1. Set up your environment variables
2. Install dependencies
3. Run the service:
   ```bash
   python run.py
   ```

## Development

```bash
# Run in development mode
uvicorn app:app --reload

# Run tests
pytest

# Run linting
flake8
```

## Adding a New Guardrail

To add a new guardrail to the system, follow these steps:

1. Create a new file in `src/guardrails/` for your guardrail implementation:

```python
from typing import Dict, Any
from pydantic import BaseModel, Field
from src.guardrails.base import (
    Guardrail, 
    GuardrailCapability, 
    ValidationResult,
    TransformationResult
)

# Define options schema for your guardrail (optional)
class YourGuardrailOptions(BaseModel):
    option1: str = Field(
        default="default_value",
        description="Description of option1"
    )
    option2: int = Field(
        default=0,
        description="Description of option2"
    )

class YourGuardrail(Guardrail):
    def __init__(self):
        super().__init__(
            id="your_guardrail_id",
            name="Your Guardrail Name",
            description="Description of what your guardrail does"
        )
        # Add supported capabilities
        self._capabilities.add(GuardrailCapability.VALIDATE)
        self._capabilities.add(GuardrailCapability.TRANSFORM)
        # Set default options
        self._options = YourGuardrailOptions()

    def _validate(self, content: str, options: Dict[str, Any]) -> ValidationResult:
        # Merge default options with provided options
        try:
            merged_options = self._options.model_copy(update=options)
            YourGuardrailOptions.model_validate(merged_options.model_dump())
        except ValidationError as e:
            raise Exception(f"Error in Your Guardrail: {str(e)}")
        
        # Implement your validation logic here
        violations = []
        # ... your validation code ...
        
        return ValidationResult(
            passed=len(violations) == 0,
            violations=violations
        )

    def _transform(self, content: str, options: Dict[str, Any]) -> TransformationResult:
        # Implement your transformation logic here
        transformed_content = content
        # ... your transformation code ...
        
        return TransformationResult(
            transformed_content=transformed_content,
            details={
                "your_detail_key": "your_detail_value"
            }
        )
```

2. Register your guardrail in `src/api/app.py`:

```python
from src.guardrails.your_guardrail import YourGuardrail

# Add to existing guardrail registrations
registry.register(YourGuardrail())
```

3. (Optional) If your guardrail requires additional dependencies:
   - Add them to `requirements.txt`
   - Document any special installation steps
   - Add any required environment variables to `.env.example`

### Best Practices

1. **Input Validation**
   - Always validate input options using Pydantic models
   - Provide clear error messages for invalid inputs
   - Document all options and their constraints

2. **Error Handling**
   - Handle edge cases gracefully
   - Provide meaningful error messages
   - Use appropriate HTTP status codes for API errors

3. **Performance**
   - Consider batch processing implications
   - Optimize resource-intensive operations
   - Cache results when appropriate

4. **Documentation**
   - Document your guardrail's purpose and capabilities
   - Provide example requests and responses
   - Document any special configuration requirements
   - Update the API documentation if adding new endpoints

### Example: Simple Profanity Guardrail

```python
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from src.guardrails.base import (
    Guardrail,
    GuardrailCapability,
    ValidationResult,
    TransformationResult
)

class ProfanityOptions(BaseModel):
    custom_words: List[str] = Field(
        default_factory=list,
        description="Additional words to consider as profanity"
    )
    replacement: str = Field(
        default="****",
        description="Text to replace profanity with"
    )

class ProfanityGuardrail(Guardrail):
    def __init__(self):
        super().__init__(
            id="profanity",
            name="Profanity Filter",
            description="Detects and filters profanity in text"
        )
        self._capabilities.add(GuardrailCapability.VALIDATE)
        self._capabilities.add(GuardrailCapability.TRANSFORM)
        self._options = ProfanityOptions()
        self._default_profanity = {"bad", "words", "list"}

    def _validate(self, content: str, options: Dict[str, Any]) -> ValidationResult:
        merged_options = self._options.model_copy(update=options)
        all_profanity = self._default_profanity.union(set(merged_options.custom_words))
        
        words = content.lower().split()
        found_profanity = [word for word in words if word in all_profanity]
        
        return ValidationResult(
            passed=len(found_profanity) == 0,
            violations=[f"Found profanity: {word}" for word in found_profanity]
        )

    def _transform(self, content: str, options: Dict[str, Any]) -> TransformationResult:
        merged_options = self._options.model_copy(update=options)
        all_profanity = self._default_profanity.union(set(merged_options.custom_words))
        
        transformed = content
        for word in all_profanity:
            transformed = transformed.replace(word, merged_options.replacement)
        
        return TransformationResult(
            transformed_content=transformed,
            details={
                "replacement_char": merged_options.replacement,
                "custom_words_added": len(merged_options.custom_words)
            }
        )
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 