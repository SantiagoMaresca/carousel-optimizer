import React from 'react'
import { Toaster } from 'react-hot-toast'
import useAppStore from './stores/appStore'
import UploadPage from './pages/UploadPage'
import ResultsPage from './pages/ResultsPage'

function App() {
  const { currentStep } = useAppStore()

  return (
    <div className="App min-h-screen bg-gradient-dark">
      {currentStep === 'upload' && <UploadPage />}
      {currentStep === 'results' && <ResultsPage />}
      
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'rgba(15, 23, 42, 0.95)',
            color: '#fff',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(12px)',
            borderRadius: '12px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  )
}

export default App