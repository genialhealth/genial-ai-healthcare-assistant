from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.schemas import ReportContent, MedicalReport

# Initialize Gemini for report generation
gemini_report = ChatOpenAI(
    base_url=settings.GEMINI_BASE_URL,
    api_key=settings.GEMINI_API_KEY,
    model=settings.GEMINI_MODEL,
    temperature=0.2, # Slightly more creative than 0, but still focused
    max_completion_tokens=2048,
)

def generate_report_content(report: MedicalReport) -> ReportContent:
    """
    Generates narrative summaries for the patient and doctor based on the structured medical report.
    """
    
    llm = gemini_report.with_structured_output(ReportContent)
    
    # Format the input data for the LLM
    evidences_str = "\n".join([f"- {k}: {v}" for k, v in report.evidences.items()])
    
    images_str = ""
    for title, analysis in report.images_analyses.items():
        images_str += f"\nImage '{title}':\n{analysis}\n"
        
    diseases_str = ""
    for d in report.most_likely_disease:
        diseases_str += f"\n- {d.disease_name} (Likelihood: {d.match_probability}%): {d.match_reason}"

    prompt = f"""
    Based on the following medical data collected from a patient consultation, please generate two distinct summaries:

    1. **Patient Summary**: A clear, compassionate, and easy-to-understand narrative for the patient. Explain their reported symptoms, the findings from any images, and the potential conditions identified. Avoid overly complex jargon. Focus on explaining "what this means".

    2. **Clinical Summary**: A concise, professional, and technical summary for a doctor. Use standard medical terminology. Highlight the key evidences, relevant image findings (specifically mentioning if skin lesions or anomalies were detected), and the differential diagnosis rationale.

    ### Input Data
    
    **Reported Evidence:**
    {evidences_str if evidences_str else "None recorded."}

    **Image Analysis:**
    {images_str if images_str else "No images provided."}

    **Differential Diagnosis (Potential Conditions):**
    {diseases_str if diseases_str else "No specific conditions identified yet."}
    
    **General Conversation Summary:**
    {report.summary}
    """

    try:
        response: ReportContent = llm.invoke([
            SystemMessage(content="You are an expert medical consultant and writer."),
            HumanMessage(content=prompt)
        ])
        return response
    except Exception as e:
        # Fallback in case of LLM failure
        return ReportContent(
            patient_summary="We could not generate the narrative summary at this time. Please refer to the structured data below.",
            clinical_summary="Automated generation failed. Refer to raw data."
        )
