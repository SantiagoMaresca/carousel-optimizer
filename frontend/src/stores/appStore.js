import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

const useAppStore = create(
  devtools(
    (set, get) => ({
      // State
      currentStep: 'upload', // 'upload' | 'analyzing' | 'results'
      uploadedFiles: [],
      sessionId: null,
      isLoading: false,
      error: null,
      analysisResults: null,
      progress: 0,

      // Actions
      setStep: (step) => set({ currentStep: step }),
      setFiles: (files) => set({ uploadedFiles: files }),
      setSessionId: (id) => set({ sessionId: id }),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      setAnalysisResults: (results) => set({ analysisResults: results }),
      setProgress: (progress) => set({ progress }),

      // Reset store
      reset: () => set({
        currentStep: 'upload',
        uploadedFiles: [],
        sessionId: null,
        isLoading: false,
        error: null,
        analysisResults: null,
        progress: 0,
      }),

      // Computed values
      hasFiles: () => get().uploadedFiles.length > 0,
      canAnalyze: () => get().uploadedFiles.length >= 2 && get().uploadedFiles.length <= 12,
    }),
    {
      name: 'carousel-optimizer-store',
    }
  )
)

export default useAppStore