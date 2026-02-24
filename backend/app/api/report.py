from fastapi import APIRouter, Header, HTTPException, Depends, Request
from typing import Annotated, Optional
import os

from app.schemas import ApiResponse, FullReportResponse, MedicalReport, Disease
from app.services.agent.session_manager import session_manager
from app.services.report_generator import generate_report_content
from app.services.agent.tools import image_to_base64
from app.api.deps import get_current_user
from app.core.limiter import limiter

router = APIRouter()

@router.get("/generate", response_model=ApiResponse[FullReportResponse])
@limiter.limit("5/minute")
async def generate_report_endpoint(
    request: Request,
    x_session_id: Annotated[Optional[str], Header()] = None,
    current_user: str = Depends(get_current_user)
):
    if not x_session_id:
        return ApiResponse(success=False, error="No session ID provided")
    
    state = await session_manager.get_session(x_session_id)
    # Link username
    await session_manager.save_session(x_session_id, state, user_id=current_user)
    
    if "medical_report" not in state:
        return ApiResponse(success=False, error="No medical data found for this session.")
        
    internal_report = state["medical_report"]
    
    # 1. Map internal report to Pydantic model
    safe_images = {k: os.path.basename(v) for k, v in internal_report.images.items()}
    
    # Prepare Base64 images for the PDF
    images_b64 = {}
    for title, path in internal_report.images.items():
        try:
            # path is the absolute path stored in the report
            # We use the title or the safe filename as the key. Let's use the title to match the structured_data keys.
            b64_str = image_to_base64(path)
            images_b64[title] = b64_str 
        except Exception as e:
            print(f"Failed to load image {path}: {e}")
    
    structured_report = MedicalReport(
        evidences=internal_report.evidences,
        images=safe_images,
        images_analyses=internal_report.images_analyses,
        summary=internal_report.summary,
        most_likely_disease=[
            Disease(
                id=d.disease_name, 
                name=d.disease_name,
                likelihood=d.match_probability,
                reason=d.match_reason
            ) for d in internal_report.most_likely_disease
        ]
    )
    
    # 2. Generate Content via LLM
    content = generate_report_content(internal_report)
    
    return ApiResponse(
        success=True,
        data=FullReportResponse(
            content=content,
            structured_data=structured_report,
            images_base64=images_b64
        )
    )
