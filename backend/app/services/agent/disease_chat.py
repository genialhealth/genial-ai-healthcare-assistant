import google.generativeai as genai
from typing import List, AsyncGenerator, Dict
from app.core.config import settings
from app.schemas import Disease, Symptom, Message

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

async def generate_disease_chat_response(
    message: str,
    disease: Disease,
    evidences: Dict[str, str] | None,
    history: List[Message]
) -> AsyncGenerator[str, None]:
    """
    Generates a streaming response for the disease deep-dive chat using the native Gemini SDK.
    """
    

    # Format Symptoms for context
    if evidences is not None:
        symptoms_text = "\n".join([
            f"- {s}: {v}"
            for s,v in evidences.items()
        ])

    # --- Scenario 1: Initial Deep Dive Analysis ---
    if not message or message.strip() == "":
        system_instruction = f"""
        You are an expert medical AI assistant conducting a "Deep Dive" analysis for a patient.
        
        **Context:**
        - **Selected Condition:** {disease.name}
        - **Likelihood:** {disease.likelihood}%
        - **Reasoning:** {disease.reason}
        
        **Evidence Reported by the Patient:**
        {symptoms_text}
        
        **Tone:** Professional, empathetic, objective. Do not diagnose; use phrases like "This aligns with..." or "This suggests...".
        """
        
        user_prompt = f"""
        **Task:**
        Provide a structured but SHORT initial explanation of why {disease.name} is a potential match.
        
        **Output Requirements:**
        1. **Brief Introduction:** Explain the connection between the patient's key symptoms and the condition. Keep it concise.
        2. **Symptom Comparison Table (Markdown):** Create a table with 3 columns:
           - **Symptom**: The symptom name.
           - **Typical for {disease.name}?**: Yes/No/Maybe (and brief note).
           - **Patient Has It?**: Yes (details) or No.
           *Include both symptoms the patient HAS and key symptoms of the disease they might be MISSING.*
        3. **Next Steps:** A one-sentence invitation for the user to ask specific questions.
        """
        
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_instruction
        )
        
        print("--- Sending Initial Analysis Request to Gemini (Native Streaming) ---")
        response = await model.generate_content_async(user_prompt, stream=True)
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    # --- Scenario 2: Ongoing Chat ---
    else:
        system_instruction = f"""
        You are an expert medical AI assistant discussing the condition "{disease.name}" with a patient.
        
        **Patient Context:**
        - **Symptoms:**
        {symptoms_text}
        
        **Match Info:** {disease.reason}
        
        **Instructions:**
        - Answer the user's question specifically about {disease.name}.
        - Always relate your answer back to the patient's specific reported symptoms if relevant.
        - Keep answers concise but informative.
        - Use Markdown for readability.
        - If the user asks for medical advice (treatment, meds), provide general info but disclaim that you are an AI and they should see a doctor.
        """
        
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_instruction
        )

        # Convert API Messages to Gemini History
        gemini_history = []
        for msg in history:
            role = "user" if msg.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.content]})

        chat = model.start_chat(history=gemini_history)
        
        print(f"--- Sending Chat Request to Gemini (Native Streaming). History len: {len(gemini_history)} ---")
        
        response = await chat.send_message_async(message, stream=True)
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text
