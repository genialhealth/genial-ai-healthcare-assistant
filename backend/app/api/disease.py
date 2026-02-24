from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.schemas import DiseaseChatRequest, ApiResponse, DiseaseChatResponseData
from app.core.limiter import limiter
from app.services.agent.disease_chat import generate_disease_chat_response
from typing import AsyncGenerator
import json

router = APIRouter()

@router.post("/disease-chat")
@limiter.limit("5/minute")
async def disease_chat_endpoint(request: Request, disease_chat_data: DiseaseChatRequest):
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in generate_disease_chat_response(
                message=disease_chat_data.message,
                disease=disease_chat_data.disease,
                evidences=disease_chat_data.evidences,
                history=disease_chat_data.conversationHistory
            ):
                # Simple SSE format: data: <content>\n\n
                # We encode the content as JSON to handle newlines safely
                payload = json.dumps({"content": chunk})
                yield f"data: {payload}\n\n"
        except Exception as e:
            print(f"ERROR during disease chat stream: {e}")
            # Optionally send an error chunk to frontend
            error_payload = json.dumps({"error": str(e)})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
