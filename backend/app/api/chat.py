from fastapi import APIRouter, Header, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Annotated, Optional, AsyncGenerator
from app.schemas import ChatRequest, ApiResponse, ChatResponseData, Symptom, SessionResponseData, Message, MedicalReport, Disease
import uuid
import json
import time
import os
import re

from app.services.agent import chat_stream
from app.services.agent.session_manager import session_manager
from langchain_core.messages import HumanMessage, AIMessage
from app.api.deps import get_current_user
from app.core.limiter import limiter

router = APIRouter()

@router.get("/session", response_model=ApiResponse[SessionResponseData])
@limiter.limit("20/minute")
async def get_session_info(
    request: Request,
    x_session_id: Annotated[Optional[str], Header()] = None,
    current_user: str = Depends(get_current_user)
):
    if not x_session_id:
        return ApiResponse(success=False, error="No session ID provided")
    
    state = await session_manager.get_session(x_session_id)
    # Update user_id if it's missing or changed
    await session_manager.save_session(x_session_id, state, user_id=current_user)
    
    # Convert LangChain messages to API Message format
    api_messages = []
    for msg in state['messages']:
        content = ""
        role = "assistant" # Default fallback
        image_url = None
        
        # 1. Handle Dicts (deserialized JSON)
        if isinstance(msg, dict):
            content = msg.get("content", "")
            # Check for standard LangChain 'type' or our own 'role'
            msg_type = msg.get("type") or msg.get("role")
            if msg_type == "human" or msg_type == "user":
                role = "user"
            elif msg_type == "ai" or msg_type == "assistant":
                role = "assistant"
                
        # 2. Handle Objects (LangChain Classes)
        elif hasattr(msg, "content"):
            content = msg.content
            # Check .type attribute (e.g. 'human', 'ai')
            if hasattr(msg, "type"):
                if msg.type == "human":
                    role = "user"
                elif msg.type == "ai":
                    role = "assistant"
            # Fallback to class check if .type is missing/weird
            elif isinstance(msg, HumanMessage):
                role = "user"
            
        # 3. Handle Strings (Edge case)
        elif isinstance(msg, str):
            content = msg
            # In this architecture, raw strings in the message history are User inputs
            role = "user"
        
        # Extract Image URL if present in content
        # Pattern matches: \n- uploaded image: <path>
        str_content = str(content)
        # Regex to find the image path at the end of the message or on a new line
        image_match = re.search(r'\n- uploaded image: (.+)', str_content)
        
        if image_match:
            full_path = image_match.group(1).strip()
            # Extract just the filename (e.g. "image.jpg" from "uploads/image.jpg")
            filename = os.path.basename(full_path)
            
            # Set the URL to the static mount path
            image_url = f"/api/static/{filename}" 
            
            # Remove the system text from the user-facing content
            str_content = str_content.replace(image_match.group(0), "").strip()

        api_messages.append(Message(
            id=str(uuid.uuid4()), 
            role=role,
            content=str_content,
            timestamp=time.time() * 1000,
            imageUrl=image_url
        ))
        
    # Prepare Medical Report
    report_data = None
    if state.get("medical_report"):
        internal_report = state["medical_report"]
        safe_images = {k: os.path.basename(v) for k, v in internal_report.images.items()}
        
        report_data = MedicalReport(
            evidences=internal_report.evidences,
            images=safe_images,
            images_analyses=internal_report.images_analyses,
            summary=internal_report.summary,
            most_likely_disease=[
                Disease(
                    id=str(uuid.uuid4()), # Generate or use index if available
                    name=d.disease_name,
                    likelihood=d.match_probability,
                    reason=d.match_reason
                ) for d in internal_report.most_likely_disease
            ]
        )

    return ApiResponse(
        success=True, 
        data=SessionResponseData(
            messages=api_messages,
            medicalReport=report_data
        )
    )

@router.post("/chat")
@limiter.limit("25/minute")
async def chat_endpoint(
    request: Request,
    chat_data: ChatRequest,
    x_session_id: Annotated[Optional[str], Header()] = None,
    current_user: str = Depends(get_current_user)
) -> StreamingResponse:
    
    # If no session ID is provided, generate a temporary one
    session_id = x_session_id if x_session_id else str(uuid.uuid4())

    new_images = []
    if chat_data.imageBase64 is not None and chat_data.imageBase64 != "":
        new_images.append(chat_data.imageBase64)

    async def event_generator() -> AsyncGenerator[str, None]:
        async for event_json in chat_stream(
            new_message=chat_data.message,
            new_images=new_images,
            session_id=session_id,
            user_id=current_user
        ):
            # Format as Server-Sent Event
            yield f"data: {event_json}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
