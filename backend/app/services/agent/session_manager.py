import json
from typing import Optional, Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.session import UserSession
from app.services.agent.models import GraphState, MedicalReport, InformationSeek
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages user sessions using SQLite persistence.
    Serializes LangGraph state to JSON for storage.
    """

    def _serialize_message(self, message: Any) -> dict:
        """Converts a LangChain message to a JSON-serializable dict."""
        if isinstance(message, str):
            return {"type": "human", "content": message}
        
        # Get additional_kwargs if they exist
        kwargs = getattr(message, "additional_kwargs", {})

        if isinstance(message, HumanMessage):
            return {"type": "human", "content": message.content, "kwargs": kwargs}
        elif isinstance(message, AIMessage):
            return {"type": "ai", "content": message.content, "kwargs": kwargs}
        elif isinstance(message, SystemMessage):
            return {"type": "system", "content": message.content, "kwargs": kwargs}
        
        # Fallback for other types
        content = getattr(message, "content", str(message))
        return {"type": "unknown", "content": content, "kwargs": kwargs}

    def _deserialize_message(self, data: dict) -> BaseMessage:
        """Converts a dict back to a LangChain message."""
        m_type = data.get("type")
        content = data.get("content", "")
        kwargs = data.get("kwargs", {})
        if m_type == "human":
            return HumanMessage(content=content, additional_kwargs=kwargs)
        elif m_type == "ai":
            return AIMessage(content=content, additional_kwargs=kwargs)
        elif m_type == "system":
            return SystemMessage(content=content, additional_kwargs=kwargs)
        return HumanMessage(content=content, additional_kwargs=kwargs)

    def _serialize_state(self, state: GraphState) -> str:
        """Serializes GraphState to a JSON string."""
        # Convert messages to dicts
        serializable_messages = [self._serialize_message(m) for m in state.get("messages", [])]
        serializable_buffer = [self._serialize_message(m) for m in state.get("disease_buffer", [])]
        
        # Prepare the report data
        report = state.get("medical_report")
        report_data = {
            "evidences": report.evidences if report else {},
            "images": report.images if report else {},
            "images_analyses": report.images_analyses if report else {},
            "summary": report.summary if report else "",
            "most_likely_disease": [d.model_dump() for d in report.most_likely_disease] if report else [],
            "medai_raw": report.medai_raw if report else {}
        }

        # Handle information_seek serialization
        info_seek = state.get("information_seek")
        info_seek_data = None
        if info_seek:
            if isinstance(info_seek, dict):
                info_seek_data = info_seek
            elif hasattr(info_seek, "model_dump"):
                info_seek_data = info_seek.model_dump()

        data = {
            "messages": serializable_messages,
            "disease_buffer": serializable_buffer,
            "medical_report": report_data,
            "information_seek": info_seek_data,
            "report_updated": state.get("report_updated", False),
            "question_count": state.get("question_count", 0)
        }
        return json.dumps(data)

    def _deserialize_state(self, json_str: str) -> GraphState:
        """Deserializes JSON string back to GraphState."""
        data = json.loads(json_str)
        
        messages = [self._deserialize_message(m) for m in data.get("messages", [])]
        buffer = [self._deserialize_message(m) for m in data.get("disease_buffer", [])]
        
        report_data = data.get("medical_report", {})
        
        # Deserialize diseases inside the report
        diseases = []
        if "most_likely_disease" in report_data:
            from app.services.agent.models import Disease
            diseases = [Disease(**d) for d in report_data["most_likely_disease"]]

        medical_report = MedicalReport(
            evidences=report_data.get("evidences", {}),
            images=report_data.get("images", {}),
            images_analyses=report_data.get("images_analyses", {}),
            summary=report_data.get("summary", ""),
            most_likely_disease=diseases,
            medai_raw=report_data.get("medai_raw", {}),
        )
        
        # Deserialize information_seek
        info_seek_data = data.get("information_seek")
        information_seek = None
        if info_seek_data:
            information_seek = InformationSeek(**info_seek_data)

        state: GraphState = {
            "messages": messages,
            "new_user_message": None,
            "medical_report": medical_report,
            "report_updated": data.get("report_updated", False),
            "disease_buffer": buffer,
            "information_seek": information_seek,
            "question_count": data.get("question_count", 0),
            # "next_step" is not in GraphState TypedDict definition in models.py, removing it to be safe or keep if dynamic
        }
        return state

    async def get_session(self, session_id: str) -> GraphState:
        """Retrieves or creates a session from the database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(UserSession).where(UserSession.session_id == session_id))
            user_session = result.scalar_one_or_none()

            if user_session:
                try:
                    return self._deserialize_state(user_session.session_data)
                except Exception as e:
                    logger.error(f"Error deserializing session {session_id}: {e}")
            
            # Return new state if not found or error
            return {
                "messages": [],
                "new_user_message": None,
                "medical_report": MedicalReport(),
                "report_updated": False,
                "disease_buffer": [],
                "information_seek": None,
                "question_count": 0
            }

    async def save_session(self, session_id: str, state: GraphState, user_id: Optional[str] = None):
        """Saves or updates a session in the database."""
        async with AsyncSessionLocal() as db:
            json_data = self._serialize_state(state)
            
            result = await db.execute(select(UserSession).where(UserSession.session_id == session_id))
            user_session = result.scalar_one_or_none()

            if user_session:
                user_session.session_data = json_data
                if user_id:
                    user_session.user_id = user_id
            else:
                user_session = UserSession(
                    session_id=session_id,
                    user_id=user_id,
                    session_data=json_data
                )
                db.add(user_session)
            
            await db.commit()

session_manager = SessionManager()
