"""
API Schemas and Data Models.

This module defines the Pydantic models used for request validation and response 
serialization across the application's REST endpoints.
"""

from typing import List, Optional, Literal, Generic, TypeVar, Dict
from pydantic import BaseModel, Field

# --- Core Models ---

class Symptom(BaseModel):
    """Represents a medical symptom reported by the user."""
    id: str = Field(description="Unique identifier for the symptom.")
    name: str = Field(description="Clinical or common name of the symptom.")
    severity: Literal['mild', 'moderate', 'severe'] = Field(description="The perceived intensity of the symptom.")
    duration: str = Field(description="How long the symptom has been present (e.g., '3 days').")
    notes: Optional[str] = Field(default=None, description="Additional context or patient remarks.")

class Message(BaseModel):
    """Represents a single message in the chat conversation history."""
    id: str = Field(description="Unique identifier for the message.")
    role: Literal['user', 'assistant'] = Field(description="The sender's role.")
    content: str = Field(description="The text content of the message.")
    timestamp: float = Field(description="Unix timestamp (milliseconds) when the message was sent.")
    imageUrl: Optional[str] = Field(default=None, description="Path to an image attached to the message, if any.")

class Disease(BaseModel):
    """Represents a potential medical condition matching the patient's data."""
    id: str = Field(description="Identifier for the condition.")
    name: str = Field(description="The name of the medical condition.")
    likelihood: float = Field(description="Percentage confidence (0.0 to 100.0) calculated by the AI system.")
    reason: str = Field(description="Detailed clinical reasoning explaining why this condition is a potential match.")

class MedicalReport(BaseModel):
    """Encapsulates the structured medical data collected during a session."""
    evidences: Dict[str, str] = Field(description="Dictionary of symptoms and clinical findings (Title -> Description).")
    images: Dict[str, str] = Field(description="Mapping of user-friendly image titles to their internal filenames.")
    images_analyses: Dict[str, str] = Field(description="Detailed AI-generated descriptions for each uploaded image.")
    summary: str = Field(description="A brief narrative summary of the entire session.")
    most_likely_disease: List[Disease] = Field(default_factory=list, description="Ranked list of matching conditions.")

# --- Generic API Response Wrapper ---

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """Standardized envelope for all API responses."""
    success: bool = Field(description="Indicates if the request was processed successfully.")
    data: Optional[T] = Field(default=None, description="The payload of the response (schema varies by endpoint).")
    error: Optional[str] = Field(default=None, description="Error message if success is false.")

# --- Request/Response Models ---

# 1. Chat
class ChatRequest(BaseModel):
    """Payload for initiating or continuing a chat session."""
    message: str = Field(description="The user's input text.")
    imageBase64: Optional[str] = Field(default=None, description="Optional base64-encoded image attached to the input.")

class ChatResponseData(BaseModel):
    """Payload returned by the chat endpoint (if not using streaming)."""
    message: str = Field(description="The AI assistant's response text.")
    extractedSymptoms: Optional[List[Symptom]] = Field(default=None, description="Any new symptoms identified in this turn.")

# 2. Disease Chat
class DiseaseChatRequest(BaseModel):
    """Request schema for asking specific questions about a identified condition."""
    message: str = Field(description="The user's question.")
    disease: Disease = Field(description="The specific condition the question pertains to.")
    evidences: Dict[str, str] = Field(description="The current clinical evidence context.")
    conversationHistory: List[Message] = Field(description="Recent history for context-aware answering.")

class DiseaseChatResponseData(BaseModel):
    """Response schema for disease-specific queries."""
    message: str = Field(description="The AI's answer.")

# 3. Session
class SessionResponseData(BaseModel):
    """Complete session state used for recovery or initial UI load."""
    messages: List[Message] = Field(description="All messages in the current conversation.")
    medicalReport: Optional[MedicalReport] = Field(default=None, description="The most recent structured report.")

# 4. Report Generation
class ReportContent(BaseModel):
    """The generated narrative content for a medical report."""
    patient_summary: str = Field(description="A compassionate, plain-language summary for the patient.")
    clinical_summary: str = Field(description="A technical, concise summary for a healthcare provider.")

class FullReportResponse(BaseModel):
    """Complete response containing narrative summaries, structured data, and assets."""
    content: ReportContent = Field(description="The narrative summaries.")
    structured_data: MedicalReport = Field(description="The raw data used to generate the report.")
    images_base64: Dict[str, str] = Field(default_factory=dict, description="Assets required for report rendering (Title -> Base64).")

# 5. Auth
class UserLogin(BaseModel):
    """Authentication request credentials."""
    username: str = Field(description="User's unique username.")
    password: str = Field(description="User's plaintext password.")

class AuthResponseData(BaseModel):
    """Result of an authentication attempt."""
    username: str = Field(description="The authenticated username.")
    message: str = Field(description="Login status message.")
    access_token: Optional[str] = Field(default=None, description="JWT access token required for subsequent requests.")
