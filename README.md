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

Validates an LLM response against specified guardrails and returns whether it passes or fails.

**Request Body:**
```json
{
  "content": "LLM response text",
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

**Response:**
```json
{
  "is_valid": boolean,
  "failed_guardrails": ["string"],
  "details": {
    "guardrail_id": {
      "passed": boolean,
      "violations": ["string"]
    }
  }
}
```

### 3. Transform Response
```http
POST /api/v1/transform
```

Applies specified transformations to make the content compliant with guardrails.

**Request Body:**
```json
{
  "content": "LLM response text",
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

**Response:**
```json
{
  "transformed_content": "string",
  "applied_transformations": ["string"],
  "details": {
    "guardrail_id": {
      "details": {}
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

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 