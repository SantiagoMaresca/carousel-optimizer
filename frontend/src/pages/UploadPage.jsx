import React from 'react'
import useAppStore from '../stores/appStore'
import FileDropzone from '../components/FileDropzone'
import LoadingSpinner from '../components/LoadingSpinner'
import AnalyzingView from '../components/AnalyzingView'
import ErrorPage from './ErrorPage'
import { apiService } from '../services/api'
import { Sparkles, ArrowRight, Image as ImageIcon, Upload } from 'lucide-react'
import toast from 'react-hot-toast'

const UploadPage = () => {
  const {
    uploadedFiles,
    setFiles,
    sessionId,
    setSessionId,
    isLoading,
    setLoading,
    error,
    setError,
    setStep,
    step,
    canAnalyze,
    reset
  } = useAppStore()

  const handleFilesSelected = (newFiles) => {
    const updatedFiles = [...uploadedFiles, ...newFiles]
    setFiles(updatedFiles)
  }

  const handleRemoveFile = (index) => {
    const updatedFiles = uploadedFiles.filter((_, i) => i !== index)
    setFiles(updatedFiles)
  }

  const handleUpload = async () => {
    if (!canAnalyze()) {
      toast.error('Please select 2-12 images to analyze')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Upload files - session is created automatically by the API
      const uploadResponse = await apiService.uploadFiles(uploadedFiles)
      console.log('Upload response:', uploadResponse)
      
      const newSessionId = uploadResponse.session_id
      setSessionId(newSessionId)
      
      if (uploadResponse.success_count > 0) {
        toast.success(`Uploaded ${uploadResponse.success_count} images successfully`)
        // Move to analysis (don't stop loading, analysis will handle it)
        await handleAnalyze(newSessionId)
      } else {
        throw new Error('No images were uploaded successfully')
      }
    } catch (error) {
      console.error('Upload failed:', error)
      console.error('Error details:', error.response?.data || error.message)
      setError(error.message || 'Upload failed')
      toast.error(error.response?.data?.detail || error.message || 'Upload failed. Please try again.')
      setLoading(false) // Only stop loading on error
    }
  }

  const handleAnalyze = async (currentSessionId = sessionId) => {
    if (!currentSessionId) {
      toast.error('No session found. Please upload files first.')
      return
    }

    setLoading(true)
    setStep('analyzing')
    toast.loading('Analyzing images with AI... This may take a few seconds', { id: 'analyzing', duration: 15000 })

    try {
      const analysisResponse = await apiService.analyzeImages(currentSessionId)
      
      // Store analysis results in the store
      useAppStore.getState().setAnalysisResults(analysisResponse)
      
      toast.dismiss('analyzing')
      toast.success(`Analysis complete! Processed ${analysisResponse.images.length} images`)
      setStep('results')
    } catch (error) {
      console.error('Analysis failed:', error)
      setError(error.message || 'Analysis failed')
      toast.dismiss('analyzing')
      toast.error('Analysis failed. Please try again.')
      setStep('upload')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    reset()
    toast.success('Reset complete. You can upload new images.')
  }

  // Show analyzing view when analyzing
  if (step === 'analyzing') {
    return <AnalyzingView />
  }

  // Show error page if there's an error
  if (error && step === 'upload') {
    return <ErrorPage error={error} onRetry={handleReset} />
  }

  return (
    <div className="min-h-screen bg-gradient-dark relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '3s' }}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-accent-purple/10 rounded-full blur-3xl animate-pulse"></div>
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Modern Header */}
        <div className="text-center mb-16 animate-fade-in">
          <div className="flex items-center justify-center mb-6">
            <div className="relative">
              <Sparkles className="w-12 h-12 text-primary-400 mr-4 animate-bounce-soft" />
              <div className="absolute inset-0 w-12 h-12 bg-primary-400 rounded-full blur-xl opacity-30"></div>
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
              AI Carousel Optimizer
            </h1>
          </div>
          
          <p className="text-xl text-white/70 max-w-3xl mx-auto leading-relaxed mb-8">
            <strong className="text-white">Optimize your entire product carousel</strong>, not just individual images. 
            Our AI analyzes your <span className="text-gradient font-semibold">image set as a cohesive carousel</span>—detecting duplicates, 
            balancing visual diversity, and strategically ordering images to <strong className="text-primary-300">maximize engagement and conversions</strong>.
          </p>
          
          {/* Feature Pills */}
          <div className="flex flex-wrap items-center justify-center gap-3 mb-12">
            <div className="bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 text-sm text-white/80 border border-white/20">
              🎯 Carousel-Wide Optimization
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 text-sm text-white/80 border border-white/20">
              🔄 Visual Diversity Analysis
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 text-sm text-white/80 border border-white/20">
              🔍 Smart Duplicate Detection
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 text-sm text-white/80 border border-white/20">
              📊 Strategic Positioning
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 text-sm text-white/80 border border-white/20">
              💰 Conversion-Focused Order
            </div>
          </div>
        </div>

        {/* Main Upload Section */}
        <div className="card-glass p-8 mb-8 animate-slide-up">
          <FileDropzone
            onFilesSelected={handleFilesSelected}
            selectedFiles={uploadedFiles}
            onRemoveFile={handleRemoveFile}
            isLoading={isLoading}
          />
        </div>

        {/* Action Section */}
        {uploadedFiles.length > 0 && (
          <div className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <div className="flex flex-col lg:flex-row justify-between items-center gap-6 mb-8">
              {/* File Count & Status */}
              <div className="flex items-center space-x-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-xl px-6 py-3 border border-white/20">
                  <div className="text-white/60 text-sm mb-1">Files Selected</div>
                  <div className="text-2xl font-bold text-white">
                    {uploadedFiles.length}
                    <span className="text-white/60 text-base font-normal ml-1">/ 12</span>
                  </div>
                </div>
                
                {uploadedFiles.length >= 2 && (
                  <div className="status-success animate-scale-in">
                    Ready to analyze ✓
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleReset}
                  disabled={isLoading}
                  className="btn-secondary"
                >
                  Clear All
                </button>

                <button
                  onClick={handleUpload}
                  disabled={!canAnalyze() || isLoading}
                  className="btn-primary flex items-center space-x-3"
                >
                  <span>Analyze Images</span>
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Enhanced Requirements Section */}
        <div className="card-glass p-8 animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center mb-6">
            <div className="w-2 h-8 bg-gradient-to-b from-primary-400 to-secondary-400 rounded-full mr-4"></div>
            <h3 className="text-xl font-semibold text-white">Upload Requirements</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <div className="w-12 h-12 bg-primary-500/20 rounded-xl flex items-center justify-center mb-4">
                <ImageIcon className="w-6 h-6 text-primary-400" />
              </div>
              <h4 className="font-semibold text-white mb-2">Image Count</h4>
              <p className="text-white/60 text-sm">2-12 product images for optimal analysis</p>
            </div>
            
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <div className="w-12 h-12 bg-secondary-500/20 rounded-xl flex items-center justify-center mb-4">
                <Upload className="w-6 h-6 text-secondary-400" />
              </div>
              <h4 className="font-semibold text-white mb-2">File Formats</h4>
              <p className="text-white/60 text-sm">JPG, PNG, or WebP format supported</p>
            </div>
            
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <div className="w-12 h-12 bg-accent-purple/20 rounded-xl flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-accent-purple" />
              </div>
              <h4 className="font-semibold text-white mb-2">File Size</h4>
              <p className="text-white/60 text-sm">Maximum 8MB per image file</p>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Loading Overlay */}
      {isLoading && (
        <LoadingSpinner 
          message={sessionId ? "🔬 Analyzing your images with AI..." : "⬆️ Uploading images securely..."}
        />
      )}
    </div>
  )
}

export default UploadPage