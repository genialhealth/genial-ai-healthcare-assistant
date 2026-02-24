from typing import List, AsyncGenerator, Optional
import logging
import json
import asyncio
import os

from app.services.agent.graph import build_graph
from app.services.agent.models import GraphState, MedicalReport
from app.utils.files import save_base64_image, delete_image
from app.services.agent.session_manager import session_manager
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# state global removed

agent = build_graph()

async def chat_stream(new_message: str, new_images: List[str], session_id: str, user_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Stream chat responses from the agent.
    Yields JSON strings formatted for SSE.
    """
    # Use session_manager to get the state for this session
    state = await session_manager.get_session(session_id)

    user_message = new_message
    for img in new_images:
        try:
            # Note: save_base64_image is likely sync, but it's fast enough for now. 
            # Ideally, wrap in run_in_executor if it becomes slow.
            img_path = save_base64_image(img)
            logger.info(f"[{session_id}] Image saved in uploads: {img_path}")
            user_message += f"\n- uploaded image: {img_path}"
        except Exception as e:
            logger.error(f"[{session_id}] Image upload failed!: {e}")
            yield json.dumps({
                "type": "error",
                "payload": {"message": "Image upload failed! Please try again."}
            })
            return
    
    logger.info(f"[{session_id}] New User Message: {user_message}")
    state['new_user_message'] = HumanMessage(content=user_message)
    
    try:
        # Initial progress update
        yield json.dumps({
            "type": "progress",
            "payload": {"message": "Reading your message...", "node": "start"}
        })

        # Use astream to get updates from the graph execution
        final_state = state 
        
        async for output in agent.astream(state, stream_mode="updates"):
            for node_name, node_state in output.items():
                final_state.update(node_state) 
                
                # Check for report updates
                if final_state.get("report_updated"):
                    report = final_state["medical_report"]
                    # Map paths to filenames for the frontend
                    safe_images = {k: os.path.basename(v) for k, v in report.images.items()}
                    
                    yield json.dumps({
                        "type": "report_update",
                        "payload": {
                            "evidences": report.evidences,
                            "images": safe_images,
                            "images_analyses": report.images_analyses,
                            "summary": report.summary
                        }
                    })

                # Yield progress updates indicating what is happening NEXT or current status
                if node_name == "pre-report-update":
                    if final_state.get("report_updated"):
                        yield json.dumps({
                            "type": "progress",
                            "payload": {"message": "Updating medical records...", "node": node_name}
                        })
                    else:
                        yield json.dumps({
                            "type": "progress",
                            "payload": {"message": "Preparing response...", "node": node_name}
                        })
                elif node_name == "image-analysis":
                    yield json.dumps({
                        "type": "progress",
                        "payload": {"message": "Checking medical knowledge...", "node": node_name}
                    })
                elif node_name == "disease-suggestion":
                     yield json.dumps({
                        "type": "progress",
                        "payload": {"message": "Evaluating possibilities...", "node": node_name}
                    })
                elif node_name == "process-diagnosis":
                    diseases = final_state.get("medical_report", {}).most_likely_disease
                    latest_disease = diseases[-1].disease_name if diseases else "condition"
                    
                    # Emit diagnosis update event for the frontend
                    yield json.dumps({
                    "type": "diagnosis_update",
                        "payload": {
                            "diseases": [
                                {
                                    "id": str(i), 
                                    "name": d.disease_name,
                                    "likelihood": d.match_probability,
                                    "reason": d.match_reason
                                } for i, d in enumerate(sorted(diseases, key=lambda d:d.match_probability, reverse=True))
                            ]
                        }
                    })

                    yield json.dumps({
                        "type": "progress",
                        "payload": {"message": f"Found potential match: {latest_disease}", "node": node_name}
                    })
                elif node_name == "sort-disease":
                    diseases = final_state.get("medical_report", {}).most_likely_disease
                    latest_disease = diseases[-1].disease_name if diseases else "condition"
                    
                    # Emit diagnosis update event for the frontend
                    yield json.dumps({
                        "type": "diagnosis_update",
                        "payload": {
                            "diseases": [
                                {
                                    "id": str(i), 
                                    "name": d.disease_name,
                                    "likelihood": d.match_probability,
                                    "reason": d.match_reason
                                } for i, d in enumerate(diseases)
                            ]
                        }
                    })
                elif node_name == "info-seek":
                    yield json.dumps({
                        "type": "progress",
                        "payload": {"message": "Formulating next steps...", "node": node_name}
                    })
                elif node_name == "interview":
                    yield json.dumps({
                        "type": "progress",
                        "payload": {"message": "Sending reply...", "node": node_name}
                    })

        # Update the session manager with the final state
        await session_manager.save_session(session_id, final_state, user_id=user_id)
        
        # Yield the final result
        last_msg_obj = final_state['messages'][-1]
        last_message_content = last_msg_obj.content
        
        # Extract suggested actions from metadata if they exist
        suggested_actions = getattr(last_msg_obj, "additional_kwargs", {}).get("suggested_actions", [])
        
        yield json.dumps({
            "type": "result",
            "payload": {
                "message": last_message_content,
                "extractedSymptoms": None,
                "suggestedActions": suggested_actions
            }
        })

    except Exception as e:
        import traceback
        logger.error(f"[{session_id}] Agent failed!: {e}")
        logger.error(traceback.format_exc())
        yield json.dumps({
            "type": "error",
            "payload": {"message": "Assistant failed! Please try again."}
        })
