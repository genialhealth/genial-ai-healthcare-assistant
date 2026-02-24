import json
from typing import List, Dict, Collection
import requests
import base64
import mimetypes
from pathlib import Path
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.core.config import settings

def image_to_base64(image_path: str) -> str:
    """
    Convert any image file to a base64 data URL usable by language models.
    Supports png, jpg, jpeg, webp, gif, bmp, tiff, etc.
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Guess MIME type from filename
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type is None:
        raise ValueError(f"Could not determine MIME type for {image_path}")

    with path.open("rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"

def analyze_skin_image(image_bytes: bytes) -> Dict | List:
    url = f"{settings.MEDAI_URL}/classify"
    try:
        response = requests.post(url, files={"file": image_bytes}, timeout=5)
        response.raise_for_status()
        data = response.json()

        return data
    
    except requests.exceptions.RequestException as e:
        print(f"Image Processing ERROR: {e}")
        return None
    
def get_recent_conversation_string(messages: Collection[BaseMessage], count=10) -> str:
    output_items = []
    for msg in messages[-1*count:]:
        if isinstance(msg, HumanMessage):
            output_items.append(f"**Patient:** {msg.content}")
        elif isinstance(msg, AIMessage):
            output_items.append(f"**Assistant:** {msg.content}")
    return "\n".join(output_items)

