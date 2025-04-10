from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Optional, Union
from src.guardrails.base import GuardrailRegistry
from src.guardrails.pii import PIIGuardrail
from src.guardrails.topic import TopicGuardrail
from src.guardrails.word_filter import WordFilterGuardrail

app = FastAPI(
    title="LLM Guardrails Service",
    description="A service for implementing safety and quality controls on Large Language Model outputs",
    version="1.0.0"
)

# Initialize registry and register guardrails
registry = GuardrailRegistry()
registry.register(PIIGuardrail())
registry.register(TopicGuardrail())
registry.register(WordFilterGuardrail())

class ValidateRequest(BaseModel):
    content: Union[str, List[str]]
    guardrails: List[str]
    options: Optional[Dict[str, Any]] = None

    @field_validator('content')
    def validate_content(cls, v):
        if isinstance(v, list):
            if not v:
                raise ValueError("Content list cannot be empty")
            if not all(isinstance(item, str) for item in v):
                raise ValueError("All items in content list must be strings")
        return v

class TransformRequest(BaseModel):
    content: Union[str, List[str]]
    guardrails: List[str]
    options: Optional[Dict[str, Any]] = None

    @field_validator('content')
    def validate_content(cls, v):
        if isinstance(v, list):
            if not v:
                raise ValueError("Content list cannot be empty")
            if not all(isinstance(item, str) for item in v):
                raise ValueError("All items in content list must be strings")
        return v

@app.get("/api/v1/guardrails")
async def list_guardrails():
    """List all available guardrails and their capabilities."""
    return {"guardrails": registry.list_all()}

@app.post("/api/v1/validate")
async def validate_content(request: ValidateRequest):
    """Validate content against specified guardrails."""
    # Convert single string to list for uniform processing
    contents = request.content if isinstance(request.content, list) else [request.content]
    
    # Initialize results
    results = {
        "is_valid": True,
        "failed_guardrails": [],
        "details": {}
    }
    
    # Process each content item
    for idx, content in enumerate(contents):
        content_results = {
            "passed": True,
            "violations": [],
            "guardrail_details": {}
        }
        
        for guardrail_id in request.guardrails:
            guardrail = registry.get(guardrail_id)
            if not guardrail:
                raise HTTPException(status_code=400, detail=f"Unknown guardrail: {guardrail_id}")
                
            try:
                # Get guardrail-specific options
                options = request.options.get(guardrail_id, {}) if request.options else {}
                
                validation_result = guardrail.validate(content, options)
                content_results["guardrail_details"][guardrail_id] = {
                    "passed": validation_result.passed,
                    "violations": validation_result.violations
                }
                
                if not validation_result.passed:
                    content_results["passed"] = False
                    if guardrail_id not in results["failed_guardrails"]:
                        results["failed_guardrails"].append(guardrail_id)
            except NotImplementedError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Guardrail {guardrail_id} does not support validation"
                )
        
        # Store results for this content item
        results["details"][f"content_{idx}"] = content_results
        if not content_results["passed"]:
            results["is_valid"] = False
    
    return results

@app.post("/api/v1/transform")
async def transform_content(request: TransformRequest):
    """Transform content using specified guardrails."""
    # Convert single string to list for uniform processing
    contents = request.content if isinstance(request.content, list) else [request.content]
    
    results = {
        "transformed_contents": [],
        "applied_transformations": [],
        "details": {}
    }
    
    # Process each content item
    for idx, content in enumerate(contents):
        current_content = content
        content_details = {}
        
        for guardrail_id in request.guardrails:
            guardrail = registry.get(guardrail_id)
            if not guardrail:
                raise HTTPException(status_code=400, detail=f"Unknown guardrail: {guardrail_id}")
                
            try:
                # Get guardrail-specific options
                guardrail_options = request.options.get(guardrail_id, {}) if request.options else {}
                
                # Apply transformation
                result = guardrail.transform(current_content, guardrail_options)
                current_content = result.transformed_content
                
                if guardrail_id not in results["applied_transformations"]:
                    results["applied_transformations"].append(guardrail_id)
                
                content_details[guardrail_id] = {
                    "details": result.details
                }
            except NotImplementedError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Guardrail {guardrail_id} does not support transformation"
                )
        
        results["transformed_contents"].append(current_content)
        results["details"][f"content_{idx}"] = content_details
    
    # If input was a single string, return single string output for backward compatibility
    if not isinstance(request.content, list):
        results["transformed_content"] = results["transformed_contents"][0]
        del results["transformed_contents"]
    
    return results

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running."""
    # Check if all registered guardrails are properly initialized
    guardrails_status = {}
    for guardrail in registry._guardrails.values():
        try:
            if hasattr(guardrail, 'model') and hasattr(guardrail.model, 'is_model_loaded'):
                guardrails_status[guardrail.id] = guardrail.model.is_model_loaded()
            else:
                guardrails_status[guardrail.id] = True
        except Exception:
            guardrails_status[guardrail.id] = False
    
    return {
        "status": "healthy",
        "guardrails": guardrails_status
    } 