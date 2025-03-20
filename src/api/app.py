from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.guardrails.base import GuardrailRegistry
from src.guardrails.pii import PIIGuardrail
from src.guardrails.topic import TopicGuardrail

app = FastAPI(
    title="LLM Guardrails Service",
    description="A service for implementing safety and quality controls on Large Language Model outputs",
    version="1.0.0"
)

# Initialize registry and register guardrails
registry = GuardrailRegistry()
registry.register(PIIGuardrail())
registry.register(TopicGuardrail())

class ValidateRequest(BaseModel):
    content: str
    guardrails: List[str]
    options: Optional[Dict[str, Any]] = None

class TransformRequest(BaseModel):
    content: str
    guardrails: List[str]
    options: Optional[Dict[str, Any]] = None

@app.get("/api/v1/guardrails")
async def list_guardrails():
    """List all available guardrails and their capabilities."""
    return {"guardrails": registry.list_all()}

@app.post("/api/v1/validate")
async def validate_content(request: ValidateRequest):
    """Validate content against specified guardrails."""
    results = {
        "is_valid": True,
        "failed_guardrails": [],
        "details": {}
    }
    
    for guardrail_id in request.guardrails:
        guardrail = registry.get(guardrail_id)
        if not guardrail:
            raise HTTPException(status_code=400, detail=f"Unknown guardrail: {guardrail_id}")
            
        try:
            # Get guardrail-specific options
            options = request.options.get(guardrail_id, {}) if request.options else {}
            
            validation_result = guardrail.validate(request.content, options)
            results["details"][guardrail_id] = {
                "passed": validation_result.passed,
                "violations": validation_result.violations
            }
            
            if not validation_result.passed:
                results["is_valid"] = False
                results["failed_guardrails"].append(guardrail_id)
        except NotImplementedError:
            raise HTTPException(
                status_code=400,
                detail=f"Guardrail {guardrail_id} does not support validation"
            )
    
    return results

@app.post("/api/v1/transform")
async def transform_content(request: TransformRequest):
    """Transform content using specified guardrails."""
    content = request.content
    applied = []
    options = {}
    
    for guardrail_id in request.guardrails:
        guardrail = registry.get(guardrail_id)
        if not guardrail:
            raise HTTPException(status_code=400, detail=f"Unknown guardrail: {guardrail_id}")
            
        try:
            # Get guardrail-specific options
            guardrail_options = request.options.get(guardrail_id, {}) if request.options else {}
            
            # Apply transformation
            result = guardrail.transform(content, guardrail_options)
            content = result.transformed_content
            applied.append(guardrail_id)
            options[guardrail_id] = {
                "details": result.details
            }
        except NotImplementedError:
            raise HTTPException(
                status_code=400,
                detail=f"Guardrail {guardrail_id} does not support transformation"
            )
    
    return {
        "transformed_content": content,
        "applied_transformations": applied,
        "details": options
    }

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