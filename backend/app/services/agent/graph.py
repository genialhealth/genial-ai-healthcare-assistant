# graph_agent.py
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
import os

from app.core.config import settings
from app.services.agent.models import GraphState, PreReportUpdateLLMResponse, MedicalReport, ImageDescriptionLLMResponse, ImageCategory, DiseaseCollection, InformationSeek, DiseaseSuggestionLLMResponse, YesNo
from app.services.agent.tools import analyze_skin_image, get_recent_conversation_string, image_to_base64

import logging
logger = logging.getLogger(__name__)

# --- LLMs ---
medgemma = ChatOpenAI(
    base_url=settings.MEDGEMMA_27_URL,
    api_key=settings.MEDGEMMA_27_API_KEY,
    model=settings.MEDGEMMA_27_NAME,
    temperature=0.1,
    max_completion_tokens=2048,
)

medgemma4 = ChatOpenAI(
    base_url=settings.MEDGEMMA_4_URL,
    api_key=settings.MEDGEMMA_4_API_KEY,
    model=settings.MEDGEMMA_4_NAME,
    temperature=0,
    max_completion_tokens=2048,
)

gemini = ChatOpenAI(
    base_url=settings.GEMINI_BASE_URL,
    api_key=settings.GEMINI_API_KEY,
    model=settings.GEMINI_MODEL,
    temperature=0.1,
    max_completion_tokens=2048,
)

# --- NODES ---

def pre_report_update_node(state: GraphState) -> GraphState:
    """
    Extracts clinical findings and image references from the user's latest input.
    
    This node acts as a parser that identifies new medical evidence (symptoms, history)
    and image attachments from the conversation. It updates the medical report
    incrementally without providing any diagnosis.
    
    Args:
        state: The shared graph state containing the report and message history.
        
    Returns:
        GraphState: The updated state with new evidences and image paths.
    """

    state["report_updated"] = False
    report = state["medical_report"]
    current_evidence_list = report.get_evidences()
    current_images = report.get_images()

    llm = gemini.with_structured_output(PreReportUpdateLLMResponse)
    system_instruction = f"""
    # ROLE
    You are a Medical Data Extraction Assistant. Your goal is to extract clinical information from a patient interview to update a structured medical report.

    # OBJECTIVE
    Identify new or updated medical evidence and image information from the most recent user message.

    # DATA EXTRACTION RULES
    For every item in `evidence_list`:
    - **evidence_title**: Use a concise medical term (e.g., "Shortness of breath", "Lower back pain", "Nausea").
    - **evidence_value**: State the status (Present/Absent) and include specific details provided by the patient (e.g., "Present; started 3 days ago, sharp pain, 7/10 severity" or "Absent; denies having any fever").

    For every item in `image_list`:
    - **image_title**: A brief description of what the image shows according to the user.
    - **image_path**: Extract the exact filename or path identifier mentioned in the conversation metadata (e.g., "input_file_0.png").
    - Do not rename existing images.

    # CONSTRAINTS
    - **NO DIAGNOSIS**: Record exactly what the user reports. Do not infer underlying conditions (e.g., record "Chest pressure," not "Possible heart attack").
    - **INCREMENTAL UPDATES**:
        - Compare findings with the CURRENT REPORT below.
        - If the user provides NEW details for an existing title, include it with the updated value.
        - If the user mentions something entirely new, add it.
        - If the user denies a symptom, set value to "Absent".
        - If the user is not sure or does not know the answer, set value to "Not Sure".
        - Never change the image_title of an existing image.
        - Never add an existing image (i.e. image with the same file path) again.
    - **EMPTY STATE**: If the latest message contains no new medical information (e.g., "Hello", "Thanks"), return null or empty lists for `evidence_list` and `image_list`.

    # CURRENT REPORT (FOR REFERENCE)
    <current_evidence_list>
    {current_evidence_list}
    </current_evidence_list>

    <current_images>
    {current_images}
    </current_images>

    # RECENT CONVERSATION HISTORY
    {get_recent_conversation_string(state['messages'])}

    # TASK
    Analyze the latest user message and provide the structured update.
    """

    try:
        response: PreReportUpdateLLMResponse = llm.invoke([
            SystemMessage(content=system_instruction),
            state["new_user_message"]
        ])

        if response.evidence_list is not None:
            for evidence in response.evidence_list:
                state["medical_report"].evidences[evidence.evidence_title] = evidence.evidence_value
                state["report_updated"] = True
            
        if response.image_list is not None:
            for image in response.image_list:
                if image.image_path and os.path.exists(image.image_path):
                    state["medical_report"].images[image.image_title] = image.image_path
                    state["medical_report"].images_analyses[image.image_title] = ""
                    state["report_updated"] = True

        state["messages"].append(state["new_user_message"])
        state["new_user_message"] = None
        
        return state
    
    except Exception as e:
        return state
    
def image_analysis_node(state: GraphState) -> GraphState:
    """
    Performs multi-modal analysis on any newly uploaded images.
    
    This node processes images that do not yet have an analysis. It uses:
    1. MedGemma 4B: For generating a professional title and detailed clinical description.
    2. Genial Team AI: For specific disease classification if the image contains skin.
    3. Gemini: To rewrite raw AI predictions into natural, patient-friendly language.
    
    Args:
        state: The current graph state.
        
    Returns:
        GraphState: State with updated 'images_analyses' and 'medai_raw' data.
    """
    report_was_updated = state["report_updated"]

    state["report_updated"] = False

    report = state["medical_report"]
    analyses = report.images_analyses
    all_image_names = list(report.images)

    for image_name in all_image_names:
        if image_name not in analyses or analyses[image_name] == "":
            # initialization
            analyses[image_name] = ""

            # First analyze with MedGemma 4b (description and disease)
            image_base64 = report.get_image_base64(image_name)
            llm = medgemma4.with_structured_output(ImageDescriptionLLMResponse)

            system_instruction = """
            # ROLE
            You are a Medical Imaging and Diagnostics Specialist.
            Provide a structured, objective analysis of a patient-provided image for a clinical report.
            If the content contains signs or markers of some disease, predict the top-5 among the most likely disease.

            ## FIELD-SPECIFIC GUIDELINES
            1. **image_title**: 
            - Provide a concise, professional title (e.g., "Complete Blood Count Report", "Lateral View of Left Ankle", "Dermatological Photo of Forearm").
            
            2. **image_description**: 
            - Provide a structured analysis using Markdown bullet points.
            - **For Lab/Document Results**: Extract key markers, values, and indicate if they are outside reference ranges (High/Low).
            - **For Clinical Photos (Skin/External)**: Describe morphology (color, shape, size), texture (scaly, smooth, raised), and borders.
            - **For Radiology (X-ray/MRI)**: Describe anatomical orientation and visible abnormalities (e.g., opacities, fractures).
            - **For Medications**: Identify name, dosage, and instructions if visible.
            
            3. **has_skin**: 
            - Set to `true` if the image displays external body skin, rashes, lesions, or wounds.
            - Set to `false` for non-skin photos such as internal radiology, lab papers, etc.

            ## CRITICAL CONSTRAINTS
            - **NON-DIAGNOSTIC**: Describe observations only. Do not provide a diagnosis (e.g., say "Erythematous rash" instead of "Eczema").
            - **OBJECTIVITY**: Use clinical terminology. Avoid subjective language like "looks painful" or "scary."
            - **DATA INTEGRITY**: If text in a document is illegible or the image is too blurry to analyze, state: "Image quality insufficient for detailed analysis" within the `image_description`.
            - **BREVITY**: Be thorough but concise. A doctor should be able to scan this in seconds.

            ## DISEASES OUPUT constraints
            - Suggest a list of at most five disease with their likelihood score.

            """

            user_prompt = "Analyze this image"

            content = [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_base64}
                }
            ]

            try:
                response: ImageDescriptionLLMResponse = llm.invoke([SystemMessage(content=system_instruction), HumanMessage(content=content)])
                if response.image_title and response.image_title != image_name:
                    # replace image title
                    report.images[response.image_title] = report.images[image_name]
                    report.images_analyses[response.image_title] = ""
                    del report.images[image_name]
                    del report.images_analyses[image_name]
                    
                    image_name = response.image_title
                
                analyses[image_name] = f"{response.image_description}"

                # if response.top_5_disease is not None and len(response.top_5_disease) > 0:
                    # report.medai_raw[image_name] = json.dumps({"ai_predictions": [item.model_dump() for item in response.top_5_disease[:5]]}, indent=2)
                if response.diseases:
                    report.medai_raw[image_name] = response.diseases

                if response.has_skin:   # run genial team ai and replace with medgemma predictions
                    try:
                        medai_response = analyze_skin_image(report.get_image_bytes(image_name))
                        if medai_response is not None:
                            report.medai_raw[image_name] = json.dumps({"ai_predictions": medai_response}, indent=2)
                    except:
                        logger.error("Genial Team AI Failed!")

                state["report_updated"] = True

            except Exception as e:
                logger.error(f"MedGemma image processing failed: {e}")

            # rewrite raw data with Gemini
            if image_name in report.medai_raw and report.medai_raw[image_name] != "":
                rewrite_prompt = f"""
                You are a medical editor.
                Rewrite the following raw output from an AI vision model to be more readable and natural for a medical report.
                
                **Instructions:**
                1. Convert the raw list of diseases and scores into a descriptive summary.
                2. Don't add any title to the summary
                3. **Map the likelihood percentages/scores** to narrative phrases (e.g. High, Medium, or Low).
                4. **DONT show scores**
                5. Use markdown styling
                6. **DONT** change medical terms
                7. These results are based based on the first look on the image. Start your text in a way that user understands this (example: at first sight our vision ai ...)

                **Raw AI Output:**
                {report.medai_raw[image_name]}
                """

                try:
                    rewritten_analysis = gemini.invoke([HumanMessage(content=rewrite_prompt)])
                    analyses[image_name] += "\n\nAI Disease Prediction (first look):\n\n"
                    analyses[image_name] += rewritten_analysis.content
                    state["report_updated"] = True
                except Exception as e:
                    logger.error(f"Failed to rewrite AI results with Gemini: {e}")
    
    state["report_updated"] = report_was_updated or state["report_updated"]
    return state

def user_goal(state: GraphState) -> str:
    """Checks if user is reporting medical information or not"""
    return "yes" if state["report_updated"] else "no"

def process_question_list_node(state: GraphState) -> GraphState:
    """
    Checks the comming question in the list exisitng data.
    If the questions is answered, it will be removed from the list.
    """
    report = state['medical_report']
    if state["information_seek"] is None:
        return state
    
    questions = state["information_seek"].questions
    if len(questions) == 0:
        return state
    
    system_instruction = f"""
    # ROLE
    You are a Medical Data Extraction Assistant.
    Your goal is check if the user medical profile contains an answer to a medical question or not.

    # USER MEDICAL PROFILE
    <patient_evidence>
    {report.get_evidences()}
    </patient_evidence>

    <image_analyses>
    {report.get_images_analyses()}
    </image_analyses>

    # TASK
    Check if the given question is answered:
    - **yes**: If the answer to the question can be inferred from user medical profile. Note that if the user explicitely indicated about "not knowing/not sure" in their profile, it is a valid answer to the question.
    - **no**: otherwise.
    """
    
    got_an_answer = False
    while len(questions) > 0:
        question = questions[-1]
        user_message = f"Verify the following question based on the user medical profile:\n\n**Question**: {question}"
        llm = gemini.with_structured_output(YesNo)
        try:
            response: YesNo = llm.invoke([
                SystemMessage(content=system_instruction),
                HumanMessage(content=user_message)
            ])

            if response.answer == 'yes':
                state['question_count'] += 1
                got_an_answer = True
                questions.pop()

                # logger.info("QUESTION VERIFICATION NODE")
                # logger.info(f"\nquestion: {question}\tanswered: {response.answer}\n")
                # logger.info("LIST OF QUESTIONS:")
                # logger.info("\n".join(questions))
            else:
                # logger.info("QUESTION VERIFICATION NODE")
                # logger.info(f"\nquestion: {question}\tanswered: {response.answer}\n")
                # logger.info("LIST OF QUESTIONS:")
                # logger.info("\n".join(questions))
                if not got_an_answer and state["report_updated"]: # i.e. no upcoming question is answered but new evidence is collected
                    questions.clear()   # chance of invalid question list -> remove current questions (i.e. forcing analysis pipeline)
                
                return state

        except Exception as e:
            logger.error(e)

    return state

def pipeline_router(state: GraphState) -> str:
    """determines next steps"""
    if state["information_seek"] is not None and len(state["information_seek"].questions) > 0:
        return "interview"
    # if state["report_updated"]: # and (state["information_seek"] is None or len(state["information_seek"].questions) == 0):
    #     return "analysis"
    return "analysis"

def disease_suggestion_node(state: GraphState) -> GraphState:
    """
    Uses MedGemma to analyze the current report containing:
    1. Evidence list
    2. Images analysis
    3. Existing suggestions

    and report a list of most likely disease with their likelihood.
    """

    state["report_updated"] = False
    report = state["medical_report"]

    llm = medgemma.with_structured_output(DiseaseSuggestionLLMResponse)

    system_instruction = f"""
    # ROLE
    You are a Lead Diagnostic Clinician.

    #TASK
    Your task is to provide a prioritized differential diagnosis using evidence reported by patient, image descriptions, and Vision AI disease predictions.

    # DATA SOURCES
    ## evidence reported by patient
    
    {report.get_evidences()}

    ## image descriptions inside patient's medical report
    
    {report.get_images_analyses()}

    ## Disease suggested by a Vision AI model
    
    {report.get_medai_results()}

    # PROBABILITY CALCULATION
    Calculate `match_probability` (0-100) of a disease using this weighted logic:
    - **Base Score**: the ratio of patient's supporting evidence over all neccessary conditions for that disease.
    - **Clinical Dissonance**: Discard disease if the patient rejects key symptoms neccessary for this diagnosis.
    - **Symptom Breadth**: A disease that explains 4 symptoms is more probable than a disease that only explains 1.

    # VISION AI MODEL
    You are responsible to verify the outputs of the Vision model and include them in your calculations based on your evaluation.

    # CONSTRAINTS
    - **ONE-BY-ONE**: Provide exactly ONE disease per turn. Check the conversation history to avoid duplicates.
    - **TERMINATION**: If no more conditions meet the match_probability score of at least 65, set the `disease` field to `null`.
    - **LACK-OF-INFO**: **DONT** suggest a disease if you don't have information about its KEY NECCESSARY SYMPTOMS.

    # OUTPUT REQUIREMENTS
    - **index**: index of the suggested disease in the list
    - **disease**: disease information including:
        - **disease_name**: Name of the disease/illness/condition
        - **match_reason**: Two short medical sentence for supporting and key lacking evidence (if exist). **Avoid** showing numerical confidence/likelihood scores reported by AI models. Instead, use narrative phrases (e.g. low, medium, high, etc).
        - **match_probability**: An integer (0-100) calculated based on the guidelines given above.
    """
    
    user_prompt = "next disease"
    messages = state["disease_buffer"]
    # logger.info(">>>>>>>>>> DIS BUFF")
    try:
        messages.append(HumanMessage(content=user_prompt))
        response: DiseaseSuggestionLLMResponse = llm.invoke([
                SystemMessage(content=system_instruction)] + messages)
        messages.append(AIMessage(content=response.model_dump_json(indent=2)))
        # logger.info(messages)
    
    except Exception as e:
        pass
        
    return state

def process_diagnosis_node(state: GraphState) -> GraphState:
    """
    Processes the latest suggestion from disease_suggestion_node.
    Updates the medical report with the new disease match.
    """

    state["report_updated"] = False
    
    if len(state["disease_buffer"]) > 1:    # User: next then AI: prediction ===> at least 2
        last_disease_message = state["disease_buffer"][-1]
        suggestion = DiseaseSuggestionLLMResponse.model_validate_json(last_disease_message.content)
        
        # We only process valid diseases here. The loop condition handles the 'stopping' case.
        if suggestion.disease and suggestion.disease.disease_name:
            if len(state["disease_buffer"]) == 2:   # first suggestion ===> empty existing list
                # logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> EMPTYING the list")
                state["medical_report"].most_likely_disease = []
            # logger.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIS LIST BEFORE APPEND: {state["medical_report"].most_likely_disease}")
            state["medical_report"].most_likely_disease.append(suggestion.disease)
    
    return state

def sort_disease_node(state: GraphState) -> GraphState:
    """
    Sorts the list of possible disease based on the likelihood score (highest to lowest)
    """

    disease = state["medical_report"].most_likely_disease
    state["disease_buffer"] = []

    if len(disease) > 0:
        state["medical_report"].most_likely_disease = sorted(disease, key=lambda x: x.match_probability, reverse=True)
    
    return state

def loop_disease_suggestion(state: GraphState) -> str:
    if len(state["disease_buffer"]) > 1:
        last_disease_message = state["disease_buffer"][-1]
        suggestion = DiseaseSuggestionLLMResponse.model_validate_json(last_disease_message.content)
        
        # Stop condition: Invalid response, empty name, too many loops, or low probability
        if suggestion.disease is None or suggestion.disease.disease_name == "" or len(state["disease_buffer"]) > 10 or suggestion.disease.match_probability < 65:
            # state["disease_buffer"].clear()
            return "continue"
        
        # Continue loop
        return "disease-loop"
        
def information_seek_node(state: GraphState) -> GraphState:
    """
    Uses MedGemma to review the current report and possible disease and
    suggests information that knowing them is important or will improve the diagnosis results
    """
    state["report_updated"] = False
    report = state["medical_report"]

    llm = medgemma.with_structured_output(InformationSeek)

    system_instruction = f"""
    # ROLE
    You are a Clinical Triage Specialist.
    Your goal is to identify the "missing pieces" of information that will either confirm or rule out the most likely diseases in the current differential diagnosis.

    # DATA REVIEW
    <current_evidence>
    {report.get_evidences()}
    </current_evidence>

    <image_analysis>
    {report.get_images_analyses()}
    </image_analysis>

    <differential_diagnosis>
    {report.get_most_likely_disease()}
    </differential_diagnosis>

    # TASK 1: EVALUATE RELIABILITY
    Determine if further questioning is necessary. 
    - If the top-ranked disease has a probability > 85% AND there are no other diseases with a probability > 60%, the diagnosis is considered RELIABLE. 
    - In this case, return an empty list for `questions`.

    # TASK 2: GENERATE DIAGNOSTIC QUESTIONS
    If the diagnosis is NOT yet reliable, generate a list of questions (max 5) based on these rules:
    1. **ATOMICITY**: Each question must ask for exactly ONE piece of information (e.g., "Do you have a fever?" is better than "Do you have a fever or chills?").
    2. **DIFFERENTIAL FOCUS**: Focus on "Pertinent Negatives" that would rule out a highly likely condition.
    3. **CLARITY**: Use patient-friendly language. Avoid complex medical jargon.
    4. **PRIORITY**: Order questions by their diagnostic impact (the question that narrows the list the most should be first).
    5. **NOVELTY**: ONLY ask questions that you cannot find their answer in the given user medical profile.

    # CONSTRAINTS
    - Maximum 5 questions.
    - If the current information is sufficient, return an empty list.
    - Do not provide medical advice or treatments.
    """

    if state['question_count'] > 20:    # double length safety
        state["information_seek"] = None
    else:
        try:
            # We use a simple User Message because the logic is in the System Instruction
            response: InformationSeek = llm.invoke([
                SystemMessage(content=system_instruction),
                HumanMessage(content="Review the case and provide the most efficient next questions.")
            ])

            if response.questions is None or len(response.questions) == 0:
                state["information_seek"] = None
                return state
            
            response.questions = response.questions[:5] # trimming 
            state["information_seek"] = response
        
        except Exception as e:
            state["information_seek"] = None
        
    return state

def propose_message_node(state: GraphState) -> GraphState:
    """
    Proposes the next message to the patient. The message can contain:
    1. Information about their situation and report
    2. Question/Request for more information
    3. Ask for photos
    4. Suggested quick reply actions
    """
    from app.services.agent.models import InterviewResponse

    state["report_updated"] = False

    if state["new_user_message"] is not None:
        state["messages"].append(state["new_user_message"])
        state["new_user_message"] = None

    report = state["medical_report"]
    current_evidence_list = report.get_evidences()
    current_images_analyses = report.get_images_analyses()
    most_likely_disease = report.get_most_likely_disease()
    qcount = state['question_count']
    
    potential_questions = []
    hint = ""
    if state["information_seek"] is not None and len(state["information_seek"].questions) > 0:
        potential_questions = state["information_seek"].questions
        hint = potential_questions[-1]

    llm = gemini.with_structured_output(InterviewResponse)

    system_instruction = f"""
    # ROLE
    You are a professional Medical Interview Assistant. You are the bridge between the patient and a clinical diagnostic system.

    # CONTEXT
    - **Collected Evidence**: {current_evidence_list}
    - **Current Possible Conditions**: {most_likely_disease}
    - **Image Analyses:** {current_images_analyses}
    - **Expert's Desired Info (Hint)**: "{hint}"
    - **Interaction Count**: {qcount} questions asked so far.
    - **Potential Future Questions**:\n   -{"\n   -".join(potential_questions[:-1])}

    # OPERATIONAL GUIDELINES

    ## 1. Answering General Questions
    - You may provide general medical information at a General Practitioner (GP) level. 
    - Keep explanations brief and educational. 
    - Do not provide a personalized diagnosis. Use phrases like "In general, [symptom] can be associated with..."
    - Always remind the user that deep-dive details are available in the **Disease Panel**.

    ## 2. INTERVIEW FLOW & HINTS
    - If the expert system provides a "Hint", your priority is to convert that into a patient-friendly question.
    - If the user provides info, acknowledge it briefly and move to the next "Hint".
    - Avoid showing numerical confidence/likelihood scores reported by AI models. Instead, use narrative phrases (e.g. low, medium, high, etc).

    ## 3. PHOTO UPLOAD INVITATION
    - If your next question or any of the questions in the 'potential future questions' list can be answered by having a photo (example: visual signs on the body, lab report or test results, medical images, etc), **kindly suggest**s the user to upload a photo.
    - **DONT** ask for a photo that is sent before, the required evidence already exist, or you can find the answer in the existing image analysis.
    - If you need a photo for a previous reason (already asked), you MUST explain why you ask again.

    ## 3. WRAP-UP (EXIT CONDITIONS)
    You must stop the interview and provide a WRAP-UP MESSAGE if ANY of the following occur:
    - **RELIABILITY**: The expert system provides no more hints AND there are diseases with high scores in the list.
    - **FATIGUE**: The interaction count is 20 or higher. We must not annoy the patient.
    - **REPETITION/STALLING**: It is for a while the user has provided no new medical information.
    - **USER PERSISTENCE**: The user insists on deep medical details or expert opinions.

    ## 4. THE WRAP-UP MESSAGE
    When wrapping up:
    - Provide a short but structured summary of what has been recorded/found.
    - Invite the user to the **Disease Tab** to see the full results, explore conditions, and ask further questions.

    # CONSTRAINTS
    - **BREVITY**: Max 3 sentences. DONT use fillers (e.g. "I understand", "Thank you").
    - **ACTIONS**: Use `suggested_actions` ONLY when there are typical answers a user can submit to the question (e.g. Yes/No, severity). Return empty otherwise.
    - **NO DIAGNOSIS**: Never say "You have [Disease]." Always refer to "possible conditions identified by the system."
    """
    
    try:
        response: InterviewResponse = llm.invoke([
            SystemMessage(content=system_instruction),
        ]+state["messages"][-15:])

        if response.message:
            state["messages"].append(
                AIMessage(
                    content=response.message,
                    additional_kwargs={"suggested_actions": response.suggested_actions}
                )
            )

    except Exception as e:
        logger.error(f"Error in propose_message_node: {e}")
        state["messages"].append(
            AIMessage(content="I have encountered an error! Please try again later.")
        )
        
    return state


    
# --- GRAPH BUILDING ---
def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("pre-report-update", pre_report_update_node)
    workflow.add_node("image-analysis", image_analysis_node)
    workflow.add_node("disease-suggestion", disease_suggestion_node)
    workflow.add_node("process-diagnosis", process_diagnosis_node)
    workflow.add_node("sort-disease", sort_disease_node)
    workflow.add_node("info-seek", information_seek_node)
    workflow.add_node("interview", propose_message_node)
    workflow.add_node("process-questions", process_question_list_node)

    # Entry
    workflow.set_entry_point("pre-report-update")
    # workflow.set_entry_point("process-questions")

    # Edges
    workflow.add_edge("pre-report-update", "image-analysis")

    workflow.add_conditional_edges(
        "image-analysis",
        user_goal,
        {
            "yes": "process-questions",
            "no": "interview"
        }
    )

    workflow.add_conditional_edges(
        "process-questions",
        pipeline_router,
        {
            "analysis": "disease-suggestion",
            "interview": "interview"
        }
    )

    # workflow.add_edge("image-analysis", "disease-suggestion")
    workflow.add_conditional_edges(
        "disease-suggestion",
        loop_disease_suggestion,
        {
            "continue": "sort-disease",
            "disease-loop": "process-diagnosis" # Route to processing node
        }
    )
    workflow.add_edge("process-diagnosis", "disease-suggestion")

    workflow.add_edge("sort-disease", "info-seek")
    workflow.add_edge("info-seek", "interview")
    workflow.add_edge("interview", END)

    return workflow.compile()
    
