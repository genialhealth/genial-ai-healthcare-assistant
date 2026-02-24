# models.py
from typing import List, Optional, TypedDict, Annotated, Union, Dict, Literal, Callable
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
import operator
import json
from enum import Enum

from app.services.agent.tools import image_to_base64

class Disease(BaseModel):
    disease_name: str = Field(description="Name of the disease/illness")
    match_reason: str = Field(description="Why it could be a match")
    match_probability: Annotated[int, Field(description="Chance of having the disease. An integer between 0 to 100", ge=0, le=100)]

class DiseaseCollection(BaseModel):
    disease_collection: List[Disease] = []

class DiseaseSuggestionLLMResponse(BaseModel):
    index: int
    disease: Optional[Disease] = None


class YesNo(BaseModel):
    answer: Literal["yes", "no"]

class MedicalReport(BaseModel):
    """
    Keeps track of the medical report of the patient
    """
    evidences: Dict[str,str] = Field(default_factory=dict, description="keeps evidence items: (key: <evidence_title>, value: <evidence_value>)")
    images: Dict[str, str] = Field(default_factory=dict, description="keeps image path items: (key: <image_name>, value: <image_path>)")
    images_analyses: Dict[str,str] = Field(default_factory=dict, description="keeps image analysis items: (key: <image_name>, value: <image_analysis>)")
    medai_raw: Dict[str,str] = Field(default_factory=dict, description="keeps raw data of MedAI analysis: (key: <image_name>, value: <medai_analysis>)")
    summary: str = Field(default="", description="brief narrative summary of the patient situation/conversation")
    most_likely_disease: List[Disease] = Field(default_factory=list, description="keeps list of most likely disease matching patients report")

    def get_evidences(self):
        return json.dumps(self.evidences, indent=2)
    
    def update_evidence(self, title, value):
        self.evidences[title] = value

    def get_images(self):
        return json.dumps(self.images, indent=2)

    def get_image_bytes(self, image_name):
        if image_name not in self.images:
            raise Exception(f"Image name not found.\nAvailable image names:\n{self.get_image_list()}")
        with open(self.images[image_name], "rb") as f:
            return f.read()
        
    def get_image_base64(self, image_name):
        if image_name not in self.images:
            raise Exception(f"Image name not found.\nAvailable image names:\n{self.get_image_list()}")
        return image_to_base64(self.images[image_name])
    
    def add_new_image(self, image_name, image_path):
        self.images[image_name] = image_path
        self.images_analyses[image_name] = ""
    
    def get_image_analysis(self, image_name):
        if image_name not in self.images:
            raise Exception(f"Image name not found.\nAvailable image names:\n{self.get_image_list()}")
        return self.images_analyses[image_name]
    
    def get_images_analyses(self):
        return json.dumps(self.images_analyses, indent=2)

    def get_medai_results(self):
        return json.dumps(self.medai_raw, indent=2)

    def set_image_analysis(self, image_name, analysis):
        if image_name not in self.images:
            raise Exception(f"Image name not found.\nAvailable image names:\n{self.get_image_list()}")
        self.images_analyses[image_name] = analysis

    def get_summary(self):
        return self.summary
    
    def update_summary(self, new_summary):
        self.summary = new_summary

    def get_most_likely_disease(self):
        output = DiseaseCollection(disease_collection=self.most_likely_disease)
        return output.model_dump_json(indent=2)
    
    def update_most_likely_disease(self, new_list: List[Disease]):
        self.most_likely_disease = new_list

    def get_full_report(self):
        return self.model_dump_json()

class EvidenceUpdateLLMResponse(BaseModel):
    evidence_title: str = Field(description="title for the evidence provided by the patient")
    evidence_value: str = Field(description="value for the evidence provided by the patient")

class ImageUpdateLLMResponse(BaseModel):
    image_title: str = Field(description="meaningful title for the image provided by the patient")
    image_path: str = Field(description="path the image")

class PreReportUpdateLLMResponse(BaseModel):
    evidence_list: Optional[List[EvidenceUpdateLLMResponse]] = None
    image_list: Optional[List[ImageUpdateLLMResponse]] = None

class ImageCategory(str, Enum):
    SKIN = "skin"
    LAB_REPORT = "lab-report"
    OTHER = "other"

class ImageDiseaseResponse(BaseModel):
    name: str
    score: Annotated[float, Field(ge=0, le=1)]

class ImageDescriptionLLMResponse(BaseModel):
    image_description: str = Field(description="medical descriptive analysis of the image content")
    image_title: str = Field(description="a short title for the image")
    diseases: str = Field(description="list of diseases with their likelihood scores")
    has_skin: bool = Field(description="If the content contains visuals of outer body skin.")

# class InformationSeek(BaseModel):
#     information: Optional[str] = Field(default=None, description="information from patient that can improve the disease suggesstion confidence")
#     importance_reason: Optional[str] = Field(default=None, description="Why or how knowing this information is helpful")

class InformationSeek(BaseModel):
    questions: List[str] = Field(default_factory=list, description="list of diagnostic questions to be asked from a patient.")

class InterviewResponse(BaseModel):
    message: str = Field(description="The main message content for the patient")
    suggested_actions: List[str] = Field(default_factory=list, description="List of short text options for quick replies (e.g., ['Yes', 'No', 'Not sure'])")

class GraphState(TypedDict):
    messages: List[BaseMessage]
    new_user_message: Union[HumanMessage, None]
    information_seek: Union[InformationSeek, None]
    medical_report: MedicalReport
    disease_buffer: List[BaseMessage]
    report_updated: bool = False
    question_count: int = 0
