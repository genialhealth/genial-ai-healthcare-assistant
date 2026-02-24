import base64
import os
import io
import uuid
from pathlib import Path
from PIL import Image

# Read from environment variable, fallback to "uploads" if not set
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))

def save_base64_image(base64_string: str) -> str:
    """
    Decodes a base64 string, converts it to JPEG, and saves it.
    Returns the relative path to the saved file.
    """
    # Ensure directory exists (handles creation inside or outside docker)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename to prevent collisions
    filename = f"{uuid.uuid4()}.jpg"
    file_path = UPLOAD_DIR / filename
    
    try:
        # Handle the "data:image/jpeg;base64," prefix if the frontend sends it
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
            
        image_data = base64.b64decode(base64_string)
        
        # Open image using Pillow
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB (in case of PNG with transparency)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # Save as JPEG
        image.save(file_path, "JPEG", quality=100)
            
        return str(file_path)
    except Exception as e:
        # Log error or handle appropriately in your service
        raise RuntimeError(f"Failed to process and save uploaded image: {str(e)}")

def delete_image(file_path: str):
    """Utility to cleanup images if needed."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass
