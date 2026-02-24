/**
 * Global State Management Store
 * 
 * Uses Zustand to manage the application's global state, including navigation,
 * chat history, symptom tracking, medical reports, and identified conditions.
 */

import { create } from 'zustand';
import { AppState, Message, Symptom, Disease, MedicalReport } from '@/types';
import { generateId } from '@/lib/utils';

export const useGenialStore = create<AppState>((set) => ({
  // --- State Variables ---
  activeTab: 'chat',
  symptoms: [],
  messages: [],
  diseases: [],
  medicalReport: null,
  unreadReport: false,
  unreadDiagnosis: false,
  selectedDisease: null,
  diseaseMessages: [],
  chatIsLoading: false,
  chatStreamingMessage: '',
  suggestedActions: [],

  // --- Actions ---

  /** Sets the currently active navigation tab (e.g., 'chat', 'results', 'profile') */
  setActiveTab: (tab) => 
    set({ activeTab: tab }),

  /** Controls the global loading state for chat interactions */
  setChatLoading: (isLoading) =>
    set({ chatIsLoading: isLoading }),

  /** Updates the temporary message displayed during AI streaming */
  setChatStreamingMessage: (message) =>
    set({ chatStreamingMessage: message }),

  /** Sets the list of quick-reply buttons for the user */
  setSuggestedActions: (actions) =>
    set({ suggestedActions: actions }),

  /** Adds a new message to the main conversation history */
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: generateId(),
          timestamp: Date.now(),
        },
      ],
    })),

  /** Updates an existing message by its ID */
  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, ...updates } : m
      ),
    })),

  /** Adds or updates a symptom in the patient's profile */
  addSymptom: (symptom) =>
    set((state) => {
      const existingIndex = state.symptoms.findIndex(
        (s) => s.name.toLowerCase() === symptom.name.toLowerCase()
      );
      
      if (existingIndex !== -1) {
        const updatedSymptoms = [...state.symptoms];
        updatedSymptoms[existingIndex] = {
          ...updatedSymptoms[existingIndex],
          ...symptom,
          id: updatedSymptoms[existingIndex].id,
        };
        return { symptoms: updatedSymptoms };
      }
      
      return { symptoms: [...state.symptoms, symptom] };
    }),

  /** Updates symptom details (e.g., severity or duration) */
  updateSymptom: (id, updates) =>
    set((state) => ({
      symptoms: state.symptoms.map((s) =>
        s.id === id ? { ...s, ...updates } : s
      ),
    })),

  /** Removes a symptom from the profile and resets the current diagnoses */
  removeSymptom: (id) =>
    set((state) => ({
      symptoms: state.symptoms.filter((s) => s.id !== id),
      diseases: [],
    })),

  /** Updates the list of potential medical conditions matching the user's data */
  setDiseases: (diseases) =>
    set({ diseases, unreadDiagnosis: true }),

  /** Updates the structured medical report data */
  updateMedicalReport: (report) =>
    set({ medicalReport: report, unreadReport: true }),

  /** Clears the "unread" notification for the medical report */
  markReportRead: () =>
    set({ unreadReport: false }),

  /** Clears the "unread" notification for the diagnoses */
  markDiagnosisRead: () =>
    set({ unreadDiagnosis: false }),

  /** Selects a specific condition for deep-dive questioning */
  selectDisease: (disease) =>
    set({ selectedDisease: disease, diseaseMessages: [] }),

  /** Adds a message to a condition-specific (deep-dive) chat */
  addDiseaseMessage: (message) =>
    set((state) => ({
      diseaseMessages: [
        ...state.diseaseMessages,
        {
          ...message,
          id: generateId(),
          timestamp: Date.now(),
        },
      ],
    })),

  /** Clears the history of a condition-specific chat */
  clearDiseaseChat: () =>
    set({ diseaseMessages: [] }),

  /** Resets the entire store to its initial state */
  reset: () =>
    set({
      activeTab: 'chat',
      symptoms: [],
      messages: [],
      diseases: [],
      medicalReport: null,
      unreadReport: false,
      unreadDiagnosis: false,
      selectedDisease: null,
      diseaseMessages: [],
      chatIsLoading: false,
      chatStreamingMessage: '',
      suggestedActions: [],
    }),
}));
