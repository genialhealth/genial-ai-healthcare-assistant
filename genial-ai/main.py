"""
Genial Team AI - FastAPI Microservice.

This service provides a RESTful API for the MedLIP 80-Diseases Classifier.
It exposes a classification endpoint that accepts image files and returns
predicted disease classes with confidence scores.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import io
import os
from PIL import Image
from inference import DiseaseClassifier

# --- Response Models ---

class ClassificationResult(BaseModel):
    """Schema for a single disease classification result."""
    name: str
    score: float

class HealthResponse(BaseModel):
    """Schema for the health check response."""
    status: str
    model_loaded: bool

# --- App Initialization ---

app = FastAPI(
    title="Genial Team AI - Medical Image Classifier",
    description="Microservice for medical disease classification using MedLIP.",
    version="1.0.0"
)

# Global classifier instance
classifier = None

@app.on_event("startup")
async def startup_event():
    """Load the model into memory on application startup."""
    global classifier
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "model.pt")
    diseases_path = os.path.join(script_dir, "disease_names.csv")
    
    print(f"Loading model from {model_path}...")
    try:
        classifier = DiseaseClassifier(model_path, diseases_path)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")

# --- Endpoints ---

@app.post(
    "/classify",
    response_model=List[ClassificationResult],
    summary="Classify a medical image",
    description="Upload an image to receive predicted disease classifications."
)
async def classify_image(file: UploadFile = File(...)):
    """Handles image upload and classification."""
    if classifier is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    
    try:
        # Read the uploaded image bytes
        image_bytes = await file.read()
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Run inference
        results = classifier.classify(image, score_threshold=0.2, top_k=5)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description="Returns the status of the service and whether the model is loaded."
)
async def health_check():
    """Performs a basic health check."""
    return {"status": "ok", "model_loaded": classifier is not None}
