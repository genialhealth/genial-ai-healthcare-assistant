export type TabId = 'chat' | 'report' | 'results' | 'profile';

export interface Symptom {
  id: string;
  name: string;
  severity: 'mild' | 'moderate' | 'severe';
  duration: string;
  notes?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  imageUrl?: string;
  reportUpdated?: boolean;
  diagnosisUpdated?: boolean;
  updatedDiseases?: { name: string; likelihood: number }[];
}

export interface Disease {
  id: string;
  name: string;
  likelihood: number;
  reason: string;
}

export interface MedicalReport {
  evidences: Record<string, string>;
  images: Record<string, string>;
  images_analyses: Record<string, string>;
  summary: string;
  most_likely_disease: Disease[]; // New field
}

export interface AppState {
  // Navigation
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;

  // Data
  symptoms: Symptom[];
  messages: Message[];
  diseases: Disease[];
  medicalReport: MedicalReport | null;
  unreadReport: boolean;
  unreadDiagnosis: boolean;
  selectedDisease: Disease | null;
  diseaseMessages: Message[];
  
  // UI State (Global)
  chatIsLoading: boolean; // New
  chatStreamingMessage: string; // New
  suggestedActions: string[];
  
  // Actions
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  addSymptom: (symptom: Symptom) => void;
  updateSymptom: (id: string, updates: Partial<Omit<Symptom, 'id'>>) => void;
  removeSymptom: (id: string) => void;
  setDiseases: (diseases: Disease[]) => void;
  updateMedicalReport: (report: MedicalReport) => void;
  markReportRead: () => void;
  markDiagnosisRead: () => void;
  selectDisease: (disease: Disease | null) => void;
  addDiseaseMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  clearDiseaseChat: () => void;
  setChatLoading: (isLoading: boolean) => void; // New
  setChatStreamingMessage: (message: string) => void; // New
  setSuggestedActions: (actions: string[]) => void;
  reset: () => void;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface ChatRequest {
  message: string;
  imageBase64?: string;
}

export interface ChatResponse {
  message: string;
  extractedSymptoms?: Symptom[];
}

export interface AnalyzeRequest {
  symptoms: Symptom[];
  conversationHistory: Message[];
}

export interface AnalyzeResponse {
  diseases: Disease[];
}

export interface DiseaseChatRequest {
  message: string;
  disease: Disease;
  evidences: Record<string, string> | null;
  conversationHistory: Message[];
}
