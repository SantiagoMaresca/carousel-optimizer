import React, { useState } from 'react'
import useAppStore from '../stores/appStore'
import { 
  Download, 
  RotateCcw, 
  Star, 
  AlertTriangle, 
  CheckCircle,
  Eye,
  TrendingUp,
  Clock,
  Copy,
  Brain,
  Image as ImageIcon,
  X,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  Layers
} from 'lucide-react'
import toast from 'react-hot-toast'

// Helper function to extract clean filename
const getCleanFilename = (filename) => {
  if (!filename) return 'Unknown'
  // Remove UUID prefix (pattern: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx_)
  const uuidPattern = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}_/i
  return filename.replace(uuidPattern, '')
}

const ResultsPage = () => {
  const { 
    analysisResults, 
    sessionId, 
    setStep, 
    reset 
  } = useAppStore()

  const [viewMode, setViewMode] = useState('interactive') // 'carousel' | 'detailed' | 'interactive'
  const [selectedImage, setSelectedImage] = useState(null) // For modal
  const [carouselIndex, setCarouselIndex] = useState(0) // For interactive carousel navigation

  // Debug logging
  React.useEffect(() => {
    if (analysisResults) {
      console.log('📊 Analysis Results:', analysisResults)
      console.log('🖼️ Images:', analysisResults.images)
      console.log('📍 Session ID:', sessionId)
    }
  }, [analysisResults, sessionId])

  // Keyboard navigation for interactive carousel
  React.useEffect(() => {
    if (viewMode !== 'interactive') return
    
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft') {
        setCarouselIndex(prev => Math.max(0, prev - 1))
      } else if (e.key === 'ArrowRight') {
        setCarouselIndex(prev => Math.min((analysisResults.recommended_order?.length || 1) - 1, prev + 1))
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [viewMode, analysisResults])

  if (!analysisResults) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <div className="text-center card-glass p-12 max-w-md mx-4">
          <p className="text-white/60 mb-6">No analysis results found</p>
          <button onClick={() => setStep('upload')} className="btn-primary">
            Start New Analysis
          </button>
        </div>
      </div>
    )
  }

  const handleExport = () => {
    const exportData = {
      session_id: sessionId,
      timestamp: new Date().toISOString(),
      results: analysisResults,
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `carousel-analysis-${sessionId.substring(0, 8)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    toast.success('Analysis results exported successfully')
  }

  const handleStartOver = () => {
    reset()
    setStep('upload')
    toast.success('Ready for new analysis')
  }

  const averageScore = analysisResults.images?.length 
    ? analysisResults.images.reduce((acc, img) => acc + img.quality_metrics.composite_score, 0) / analysisResults.images.length
    : 0

  const duplicateCount = analysisResults.duplicates?.length || 0
  const improvementCount = analysisResults.images?.filter(img => 
    img.quality_metrics.suggestions && img.quality_metrics.suggestions.length > 0
  ).length || 0

  // Close modal when clicking outside
  const handleModalClose = () => setSelectedImage(null)

  // Render Image Detail Modal
  const renderModal = () => {
    if (!selectedImage) return null

    const imageData = analysisResults.images?.find(img => img.id === selectedImage.imageId)
    if (!imageData) return null

    const displayName = getCleanFilename(imageData.filename)
    const qualityGrade = imageData.quality_metrics.quality_grade || 'UNKNOWN'
    const gradeColor = 
      qualityGrade === 'EXCEPTIONAL' ? 'bg-green-500/20 text-green-300 border-green-500/30' :
      qualityGrade === 'PROFESSIONAL' ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' :
      qualityGrade === 'GOOD' ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' :
      qualityGrade === 'ACCEPTABLE' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' : 
      'bg-red-500/20 text-red-300 border-red-500/30'

    return (
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
        onClick={handleModalClose}
      >
        <div 
          className="card-glass max-w-5xl w-full max-h-[90vh] overflow-y-auto relative animate-slide-up"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close Button - Fixed positioning */}
          <button
            onClick={handleModalClose}
            className="sticky top-4 right-4 float-right z-50 w-12 h-12 rounded-full bg-red-500/80 hover:bg-red-600 backdrop-blur-sm flex items-center justify-center text-white transition-all shadow-lg hover:scale-110"
            title="Close"
          >
            <X className="w-6 h-6" />
          </button>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
            {/* Left: Image */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold ${
                      selectedImage.isHero 
                        ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white' 
                        : 'bg-white/20 backdrop-blur-sm text-white'
                    }`}>
                      {selectedImage.position}
                    </div>
                    {selectedImage.isHero && (
                      <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-sm font-bold px-3 py-1.5 rounded-full">
                        🏆 HERO IMAGE
                      </div>
                    )}
                  </div>
                  <h2 className="text-2xl font-bold text-white">{displayName}</h2>
                </div>
              </div>

              <div className="aspect-square bg-gradient-to-br from-dark-800 to-dark-700 rounded-xl overflow-hidden">
                {imageData.image_url ? (
                  <img 
                    src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${imageData.image_url}`}
                    alt={displayName}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <ImageIcon className="w-20 h-20 text-white/40" />
                  </div>
                )}
              </div>

              {/* File Info */}
              <div className="card-glass p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-white/60">Resolution:</span>
                  <span className="text-white font-semibold">
                    {imageData.quality_metrics.resolution[0]} × {imageData.quality_metrics.resolution[1]}
                  </span>
                </div>
                {imageData.quality_metrics.megapixels && (
                  <div className="flex justify-between">
                    <span className="text-white/60">Size:</span>
                    <span className="text-white font-semibold">{imageData.quality_metrics.megapixels.toFixed(1)} MP</span>
                  </div>
                )}
                {imageData.quality_metrics.format && imageData.quality_metrics.format !== 'unknown' && (
                  <div className="flex justify-between">
                    <span className="text-white/60">Format:</span>
                    <span className="text-white font-semibold">{imageData.quality_metrics.format}</span>
                  </div>
                )}
                {imageData.quality_metrics.file_size && imageData.quality_metrics.file_size > 0 && (
                  <div className="flex justify-between">
                    <span className="text-white/60">File Size:</span>
                    <span className="text-white font-semibold">
                      {(imageData.quality_metrics.file_size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                )}
                {imageData.quality_metrics.aspect_ratio && (
                  <div className="flex justify-between">
                    <span className="text-white/60">Aspect Ratio:</span>
                    <span className="text-white font-semibold">{imageData.quality_metrics.aspect_ratio.toFixed(2)}:1</span>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Analysis */}
            <div className="space-y-4">
              {/* Quality Score */}
              <div className="card-glass p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-white font-bold text-lg mb-2">Overall Quality Score</h3>
                    <div className={`inline-block px-3 py-1 rounded-lg text-sm font-bold border ${gradeColor}`}>
                      {qualityGrade}
                    </div>
                  </div>
                  <div className="text-5xl font-bold text-white">
                    {imageData.quality_metrics.composite_score.toFixed(1)}
                  </div>
                </div>
                <div className="w-full bg-white/10 rounded-full h-4">
                  <div 
                    className="bg-gradient-to-r from-primary-400 to-secondary-400 h-4 rounded-full transition-all"
                    style={{ width: `${imageData.quality_metrics.composite_score}%` }}
                  ></div>
                </div>
              </div>

              {/* Technical Metrics */}
              <div className="card-glass p-4">
                <h3 className="text-white font-bold mb-4 flex items-center">
                  <span className="mr-2">📊</span> Technical Analysis
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/5 p-3 rounded-lg">
                    <div className="text-white/60 text-xs mb-1">Sharpness</div>
                    <div className="text-white font-bold text-xl">{imageData.quality_metrics.blur_score.toFixed(0)}</div>
                    <div className="text-white/50 text-xs mt-1">
                      {imageData.quality_metrics.blur_score >= 500 ? '✅ Sharp' : 
                       imageData.quality_metrics.blur_score >= 300 ? '⚠️ Moderate' : '❌ Blurry'}
                    </div>
                  </div>
                  <div className="bg-white/5 p-3 rounded-lg">
                    <div className="text-white/60 text-xs mb-1">Brightness</div>
                    <div className="text-white font-bold text-xl">{imageData.quality_metrics.brightness.toFixed(0)}</div>
                    <div className="text-white/50 text-xs mt-1">
                      {imageData.quality_metrics.brightness >= 100 && imageData.quality_metrics.brightness <= 150 ? '✅ Perfect' :
                       imageData.quality_metrics.brightness < 80 ? '🔦 Dark' : 
                       imageData.quality_metrics.brightness > 170 ? '☀️ Bright' : '⚠️ OK'}
                    </div>
                  </div>
                  <div className="bg-white/5 p-3 rounded-lg">
                    <div className="text-white/60 text-xs mb-1">Contrast</div>
                    <div className="text-white font-bold text-xl">{imageData.quality_metrics.contrast.toFixed(0)}</div>
                    <div className="text-white/50 text-xs mt-1">
                      {imageData.quality_metrics.contrast >= 50 ? '✅ Excellent' :
                       imageData.quality_metrics.contrast >= 35 ? '⚠️ Moderate' : '🎨 Low'}
                    </div>
                  </div>
                  <div className="bg-white/5 p-3 rounded-lg">
                    <div className="text-white/60 text-xs mb-1">Position</div>
                    <div className="text-white font-bold text-xl">#{selectedImage.position}</div>
                    <div className="text-white/50 text-xs mt-1">
                      {selectedImage.isHero ? '🏆 Hero' : '📍 Carousel'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Position Reasoning */}
              <div className="card-glass p-4 bg-primary-500/10 border border-primary-500/30">
                <h3 className="text-primary-300 font-bold mb-3 flex items-center">
                  <span className="mr-2">🎯</span> Why This Position?
                </h3>
                <p className="text-white/90 leading-relaxed">{selectedImage.reason}</p>
              </div>

              {/* AI Recommendations */}
              {imageData.quality_metrics.suggestions && imageData.quality_metrics.suggestions.length > 0 && (
                <div className="card-glass p-4 bg-yellow-500/10 border border-yellow-500/30">
                  <h3 className="text-yellow-300 font-bold mb-3 flex items-center">
                    <span className="mr-2">💡</span> AI Recommendations
                  </h3>
                  <div className="max-h-52 overflow-y-auto space-y-2 pr-2">
                    {imageData.quality_metrics.suggestions.map((suggestion, idx) => (
                      <div key={idx} className="flex items-start space-x-2 text-white/90 text-sm leading-relaxed bg-white/5 p-3 rounded-lg">
                        <span className="text-yellow-400 flex-shrink-0">•</span>
                        <span>{suggestion}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-dark relative overflow-hidden">
      {/* Render Modal */}
      {renderModal()}

      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '3s' }}></div>
        <div className="absolute top-1/4 right-1/4 w-40 h-40 bg-accent-purple/10 rounded-full blur-3xl animate-pulse"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Modern Header */}
        <div className="mb-12 animate-fade-in">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <div className="flex items-center mb-4">
                <div className="w-3 h-8 bg-gradient-to-b from-primary-400 to-secondary-400 rounded-full mr-4"></div>
                <h1 className="text-4xl font-bold text-white">
                  🎯 Analysis Complete
                </h1>
              </div>
              <p className="text-xl text-white/70 max-w-2xl">
                Your carousel has been optimized with <span className="text-gradient font-semibold">AI-powered insights</span> and recommendations
              </p>
              {/* Debug info */}
              <p className="text-xs text-white/40 mt-2">
                Session: {sessionId?.substring(0, 8)} | Images: {analysisResults.images?.length || 0} | 
                {analysisResults.images?.[0]?.image_url ? ' ✅ URLs Present' : ' ⚠️ NO URLs - Using old data!'}
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <button
                onClick={handleExport}
                className="btn-secondary flex items-center space-x-3"
              >
                <Download className="w-5 h-5" />
                <span>Export Results</span>
              </button>
              
              <button
                onClick={handleStartOver}
                className="btn-primary flex items-center space-x-3"
              >
                <RotateCcw className="w-5 h-5" />
                <span>New Analysis</span>
              </button>
            </div>
          </div>
        </div>

        {/* Key Metrics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12 animate-slide-up">
          {/* Processing Time */}
          <div className="card-glass p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-primary-500/20 rounded-xl flex items-center justify-center">
                <Clock className="w-6 h-6 text-primary-400" />
              </div>
              <div className="text-right overflow-hidden">
                <div className="text-2xl font-bold text-white truncate">
                  {Math.round(analysisResults.processing_time_ms)}ms
                </div>
                <div className="text-white/60 text-sm">Processing Time</div>
              </div>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div className="bg-primary-400 h-2 rounded-full" style={{ width: '100%' }}></div>
            </div>
          </div>

          {/* Average Quality Score */}
          <div className="card-glass p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-secondary-500/20 rounded-xl flex items-center justify-center">
                <Star className="w-6 h-6 text-secondary-400" />
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-white">
                  {averageScore.toFixed(1)}
                </div>
                <div className="text-white/60 text-sm">Avg Quality Score</div>
              </div>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div className="bg-secondary-400 h-2 rounded-full" style={{ width: `${averageScore}%` }}></div>
            </div>
          </div>

          {/* Duplicates Found */}
          <div className="card-glass p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-yellow-500/20 rounded-xl flex items-center justify-center">
                <Copy className="w-6 h-6 text-yellow-400" />
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-white">
                  {duplicateCount}
                </div>
                <div className="text-white/60 text-sm">Duplicates Found</div>
              </div>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div className={`h-2 rounded-full ${duplicateCount === 0 ? 'bg-green-400' : 'bg-yellow-400'}`} 
                   style={{ width: '100%' }}></div>
            </div>
          </div>

          {/* Improvements Suggested */}
          <div className="card-glass p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-accent-purple/20 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-accent-purple" />
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-white">
                  {improvementCount}
                </div>
                <div className="text-white/60 text-sm">Improvements</div>
              </div>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div className="bg-accent-purple h-2 rounded-full" 
                   style={{ width: `${(improvementCount / (analysisResults.images?.length || 1)) * 100}%` }}></div>
            </div>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center justify-center mb-8 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-2 border border-white/20">
            <div className="flex items-center space-x-2">
              {[
                { key: 'carousel', label: 'Carousel View', icon: Eye },
                { key: 'interactive', label: 'Interactive', icon: Layers },
                { key: 'detailed', label: 'Detailed View', icon: Brain }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setViewMode(key)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-300 ${
                    viewMode === key
                      ? 'bg-primary-500 text-white shadow-lg'
                      : 'text-white/70 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Content */}
        <div className="animate-slide-up" style={{ animationDelay: '0.3s' }}>
          {analysisResults.recommended_order && analysisResults.recommended_order.length > 0 && (
            <div className="card-glass p-8">
              <div className="flex items-center mb-8">
                <div className="w-2 h-8 bg-gradient-to-b from-primary-400 to-secondary-400 rounded-full mr-4"></div>
                <h2 className="text-2xl font-bold text-white">Optimized Carousel Order</h2>
              </div>

              {/* Ordering Logic Explanation */}
              <div className="mb-6 card-glass p-4 bg-blue-500/10 border border-blue-500/30">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <Brain className="w-5 h-5 text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-blue-300 font-bold mb-2 flex items-center">
                      🧠 AI-Powered Ordering Logic
                    </h3>
                    <p className="text-white/80 text-sm leading-relaxed">
                      Images are <strong>not sorted by quality score alone</strong>. Our AI optimizes for <strong>engagement and conversions</strong> by:
                    </p>
                    <ul className="mt-2 space-y-1 text-white/70 text-sm">
                      <li>• <strong>Visual Diversity</strong>: Separating similar/duplicate images</li>
                      <li>• <strong>Strategic Positioning</strong>: Balancing quality with variety</li>
                      <li>• <strong>Engagement Flow</strong>: Creating rhythm that keeps users scrolling</li>
                    </ul>
                    <p className="mt-2 text-blue-300 text-xs">
                      💡 <strong>Tip:</strong> Click any image to see why it's in that specific position!
                    </p>
                  </div>
                </div>
              </div>

              {/* Carousel View */}
              {viewMode === 'carousel' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {analysisResults.recommended_order.map((item, index) => {
                    const imageData = analysisResults.images?.find(img => img.id === item.image_id)
                    if (!imageData) return null

                    // Extract clean filename using helper function
                    const displayName = getCleanFilename(imageData.filename)

                    const qualityGrade = imageData.quality_metrics.quality_grade || 'UNKNOWN'
                    const gradeColor = 
                      qualityGrade === 'EXCEPTIONAL' ? 'bg-green-500/20 text-green-300' :
                      qualityGrade === 'PROFESSIONAL' ? 'bg-blue-500/20 text-blue-300' :
                      qualityGrade === 'GOOD' ? 'bg-cyan-500/20 text-cyan-300' :
                      qualityGrade === 'ACCEPTABLE' ? 'bg-yellow-500/20 text-yellow-300' : 
                      'bg-red-500/20 text-red-300'

                    // Check if this image is marked as duplicate
                    const isDuplicate = analysisResults.duplicates?.some(
                      dup => dup.image_a === item.image_id || dup.image_b === item.image_id
                    )

                    // Get duplicate info if exists
                    const duplicateInfo = isDuplicate ? analysisResults.duplicates?.find(
                      dup => dup.image_a === item.image_id || dup.image_b === item.image_id
                    ) : null

                    return (
                      <div 
                        key={item.image_id} 
                        className="relative group cursor-pointer"
                        onClick={() => setSelectedImage({
                          imageId: item.image_id,
                          position: item.position,
                          isHero: item.is_hero,
                          reason: item.reason
                        })}
                      >
                        <div className="card-glass overflow-hidden transition-all duration-300 group-hover:scale-[1.03] group-hover:shadow-2xl flex flex-col h-full">
                          {/* Position Badge */}
                          <div className="absolute top-3 left-3 z-20">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shadow-lg ${
                              item.is_hero 
                                ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white' 
                                : 'bg-white/20 backdrop-blur-sm text-white'
                            }`}>
                              {item.position}
                            </div>
                          </div>

                          {/* Hero Badge */}
                          {item.is_hero && (
                            <div className="absolute top-3 right-3 z-20">
                              <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-xs font-bold px-2 py-1 rounded-full shadow-lg">
                                🏆 HERO
                              </div>
                            </div>
                          )}

                          {/* Duplicate Indicator */}
                          {isDuplicate && (
                            <div className="absolute top-14 right-3 z-20">
                              <div className="bg-orange-500/90 text-white text-xs font-bold px-2 py-1 rounded-full shadow-lg backdrop-blur-sm" title={`${(duplicateInfo?.similarity * 100).toFixed(0)}% similar to another image`}>
                                🔄 {(duplicateInfo?.similarity * 100).toFixed(0)}%
                              </div>
                            </div>
                          )}

                          {/* Image Display - Fixed Height */}
                          <div className="aspect-square bg-gradient-to-br from-dark-800 to-dark-700 relative overflow-hidden flex-shrink-0">
                            {imageData.image_url ? (
                              <img 
                                src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${imageData.image_url}`}
                                alt={displayName}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  console.error('❌ Image failed to load:', imageData.image_url)
                                  e.target.style.display = 'none'
                                  e.target.nextSibling.style.display = 'flex'
                                }}
                                onLoad={() => console.log('✅ Image loaded:', displayName)}
                              />
                            ) : null}
                            <div className="absolute inset-0 flex items-center justify-center" style={{ display: imageData.image_url ? 'none' : 'flex' }}>
                              <ImageIcon className="w-12 h-12 text-white/40" />
                            </div>

                            {/* Click Overlay Hint */}
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all duration-300 flex items-center justify-center">
                              <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-white/10 backdrop-blur-md px-4 py-2 rounded-full border border-white/20">
                                <div className="flex items-center space-x-2 text-white text-sm font-semibold">
                                  <Maximize2 className="w-4 h-4" />
                                  <span>Click to view details</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Image Info - Fixed Height Section */}
                          <div className="p-3 flex flex-col flex-grow">
                            <h3 className="font-semibold text-white text-sm mb-2 truncate" title={displayName}>
                              {displayName}
                            </h3>
                            
                            {/* Quality Score with Grade Badge */}
                            <div className="flex items-center justify-between mb-2 flex-shrink-0">
                              <div>
                                <span className="text-white/60 text-xs">Quality</span>
                                <div className={`inline-block ml-1.5 px-1.5 py-0.5 rounded text-[9px] font-bold ${gradeColor}`}>
                                  {qualityGrade}
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <div className="w-16 bg-white/10 rounded-full h-2">
                                  <div 
                                    className="bg-gradient-to-r from-primary-400 to-secondary-400 h-2 rounded-full transition-all"
                                    style={{ width: `${imageData.quality_metrics.composite_score}%` }}
                                  ></div>
                                </div>
                                <span className="text-white text-sm font-bold min-w-[2rem] text-right">
                                  {imageData.quality_metrics.composite_score.toFixed(1)}
                                </span>
                              </div>
                            </div>

                            {/* Position Reasoning - More Prominent */}
                            <div className="mb-2 flex-shrink-0">
                              <div className="bg-primary-500/10 border border-primary-500/30 rounded-lg p-2">
                                <div className="text-primary-300 text-[10px] font-bold mb-1">🎯 WHY POSITION #{item.position}?</div>
                                <div className="text-white/90 text-xs leading-tight">
                                  {item.reason.split('•')[0].trim()}
                                </div>
                              </div>
                            </div>

                            {/* Click Hint */}
                            <div className="mt-2 text-center text-white/30 text-[10px] group-hover:text-primary-400 transition-colors flex-shrink-0">
                              👆 Click to see full analysis
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Interactive Carousel Navigation View */}
              {viewMode === 'interactive' && analysisResults.recommended_order && analysisResults.recommended_order.length > 0 && (() => {
                const currentItem = analysisResults.recommended_order[carouselIndex]
                const currentImageData = analysisResults.images?.find(img => img.id === currentItem.image_id)
                
                if (!currentImageData) return null
                
                const displayName = getCleanFilename(currentImageData.filename)
                const qualityGrade = currentImageData.quality_metrics.quality_grade || 'UNKNOWN'
                const gradeColor = 
                  qualityGrade === 'EXCEPTIONAL' ? 'bg-green-500/20 text-green-300 border-green-500/30' :
                  qualityGrade === 'PROFESSIONAL' ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' :
                  qualityGrade === 'GOOD' ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' :
                  qualityGrade === 'ACCEPTABLE' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' : 
                  'bg-red-500/20 text-red-300 border-red-500/30'

                return (
                  <div className="space-y-6">
                    {/* Main Display Area */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      {/* Left: Large Image with Navigation */}
                      <div className="space-y-4">
                        {/* Navigation Controls */}
                        <div className="flex items-center justify-between mb-4">
                          <button
                            onClick={() => setCarouselIndex(Math.max(0, carouselIndex - 1))}
                            disabled={carouselIndex === 0}
                            className="w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-all"
                          >
                            <ChevronLeft className="w-6 h-6 text-white" />
                          </button>
                          
                          <div className="flex items-center space-x-3">
                            <div className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold shadow-xl ${
                              currentItem.is_hero 
                                ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white' 
                                : 'bg-white/20 backdrop-blur-sm text-white'
                            }`}>
                              {currentItem.position}
                            </div>
                            {currentItem.is_hero && (
                              <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-sm font-bold px-4 py-2 rounded-full shadow-lg">
                                🏆 HERO IMAGE
                              </div>
                            )}
                          </div>

                          <button
                            onClick={() => setCarouselIndex(Math.min(analysisResults.recommended_order.length - 1, carouselIndex + 1))}
                            disabled={carouselIndex === analysisResults.recommended_order.length - 1}
                            className="w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-all"
                          >
                            <ChevronRight className="w-6 h-6 text-white" />
                          </button>
                        </div>

                        {/* Main Image */}
                        <div className="aspect-square bg-gradient-to-br from-dark-800 to-dark-700 rounded-2xl overflow-hidden shadow-2xl">
                          {currentImageData.image_url ? (
                            <img 
                              src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${currentImageData.image_url}`}
                              alt={displayName}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <ImageIcon className="w-20 h-20 text-white/40" />
                            </div>
                          )}
                        </div>

                        {/* Image Info */}
                        <div className="card-glass p-4 space-y-2 text-sm">
                          <h3 className="text-xl font-bold text-white mb-3">{displayName}</h3>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="flex justify-between">
                              <span className="text-white/60">Resolution:</span>
                              <span className="text-white font-semibold">
                                {currentImageData.quality_metrics.resolution[0]} × {currentImageData.quality_metrics.resolution[1]}
                              </span>
                            </div>
                            {currentImageData.quality_metrics.megapixels && (
                              <div className="flex justify-between">
                                <span className="text-white/60">Size:</span>
                                <span className="text-white font-semibold">{currentImageData.quality_metrics.megapixels.toFixed(1)} MP</span>
                              </div>
                            )}
                            {currentImageData.quality_metrics.format && currentImageData.quality_metrics.format !== 'unknown' && (
                              <div className="flex justify-between">
                                <span className="text-white/60">Format:</span>
                                <span className="text-white font-semibold">{currentImageData.quality_metrics.format}</span>
                              </div>
                            )}
                            {currentImageData.quality_metrics.file_size && currentImageData.quality_metrics.file_size > 0 && (
                              <div className="flex justify-between">
                                <span className="text-white/60">File Size:</span>
                                <span className="text-white font-semibold">
                                  {(currentImageData.quality_metrics.file_size / 1024 / 1024).toFixed(2)} MB
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Right: Analysis */}
                      <div className="space-y-4">
                        {/* Quality Score */}
                        <div className="card-glass p-6">
                          <div className="flex items-center justify-between mb-4">
                            <div>
                              <h3 className="text-white font-bold text-lg mb-2">Overall Quality Score</h3>
                              <div className={`inline-block px-3 py-1 rounded-lg text-sm font-bold border ${gradeColor}`}>
                                {qualityGrade}
                              </div>
                            </div>
                            <div className="text-5xl font-bold text-white">
                              {currentImageData.quality_metrics.composite_score.toFixed(1)}
                            </div>
                          </div>
                          <div className="w-full bg-white/10 rounded-full h-4">
                            <div 
                              className="bg-gradient-to-r from-primary-400 to-secondary-400 h-4 rounded-full transition-all duration-500"
                              style={{ width: `${currentImageData.quality_metrics.composite_score}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* Technical Metrics */}
                        <div className="card-glass p-6">
                          <h3 className="text-white font-bold text-lg mb-4">Technical Metrics</h3>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white/5 rounded-lg p-3">
                              <div className="text-white/60 text-xs mb-1">Sharpness</div>
                              <div className="text-white text-xl font-bold">{currentImageData.quality_metrics.blur_score.toFixed(0)}</div>
                              <div className="text-primary-400 text-xs mt-1">
                                {currentImageData.quality_metrics.blur_score > 100 ? '✓ Sharp' : '⚠️ Slightly Blurry'}
                              </div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-3">
                              <div className="text-white/60 text-xs mb-1">Brightness</div>
                              <div className="text-white text-xl font-bold">{currentImageData.quality_metrics.brightness.toFixed(0)}</div>
                              <div className="text-secondary-400 text-xs mt-1">
                                {currentImageData.quality_metrics.brightness >= 80 && currentImageData.quality_metrics.brightness <= 180 ? '✓ Perfect' : '⚠️ Adjust'}
                              </div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-3">
                              <div className="text-white/60 text-xs mb-1">Contrast</div>
                              <div className="text-white text-xl font-bold">{currentImageData.quality_metrics.contrast.toFixed(0)}</div>
                              <div className="text-accent-purple text-xs mt-1">
                                {currentImageData.quality_metrics.contrast > 40 ? '✓ Excellent' : '⚠️ Low'}
                              </div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-3">
                              <div className="text-white/60 text-xs mb-1">Position</div>
                              <div className="text-white text-xl font-bold">#{currentItem.position}</div>
                              <div className="text-yellow-400 text-xs mt-1">
                                {currentItem.is_hero ? '🏆 Hero' : '📍 Optimized'}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Position Reasoning */}
                        <div className="card-glass p-6 bg-primary-500/10 border border-primary-500/30">
                          <h3 className="text-primary-300 font-bold text-lg mb-3">🎯 Why Position #{currentItem.position}?</h3>
                          <p className="text-white/90 leading-relaxed">{currentItem.reason}</p>
                        </div>

                        {/* AI Recommendations */}
                        {currentImageData.quality_metrics.suggestions && currentImageData.quality_metrics.suggestions.length > 0 && (
                          <div className="card-glass p-4 bg-yellow-500/10 border border-yellow-500/30">
                            <h3 className="text-yellow-300 font-bold mb-3 flex items-center">
                              <span className="mr-2">💡</span> AI Recommendations
                            </h3>
                            <div className="max-h-52 overflow-y-auto space-y-2 pr-2">
                              {currentImageData.quality_metrics.suggestions.map((suggestion, idx) => (
                                <div key={idx} className="flex items-start space-x-2 text-white/90 text-sm leading-relaxed bg-white/5 p-3 rounded-lg">
                                  <span className="text-yellow-400 flex-shrink-0">•</span>
                                  <span>{suggestion}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Thumbnail Navigation */}
                    <div className="card-glass p-6">
                      <h3 className="text-white font-bold text-lg mb-4 flex items-center">
                        <Layers className="w-5 h-5 mr-2" />
                        All Images ({analysisResults.recommended_order.length})
                        <span className="ml-auto text-sm text-white/60">Use ← → arrow keys to navigate</span>
                      </h3>
                      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-3">
                        {analysisResults.recommended_order.map((item, idx) => {
                          const thumbImageData = analysisResults.images?.find(img => img.id === item.image_id)
                          if (!thumbImageData) return null

                          const isSelected = idx === carouselIndex

                          return (
                            <div
                              key={item.image_id}
                              onClick={() => setCarouselIndex(idx)}
                              className={`relative cursor-pointer transition-all duration-300 ${
                                isSelected 
                                  ? 'ring-4 ring-primary-500 scale-110 shadow-2xl' 
                                  : 'hover:scale-105 hover:ring-2 hover:ring-white/30'
                              }`}
                            >
                              <div className="aspect-square bg-gradient-to-br from-dark-800 to-dark-700 rounded-lg overflow-hidden">
                                {thumbImageData.image_url ? (
                                  <img 
                                    src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${thumbImageData.image_url}`}
                                    alt={`Image ${item.position}`}
                                    className="w-full h-full object-cover"
                                  />
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center">
                                    <ImageIcon className="w-6 h-6 text-white/40" />
                                  </div>
                                )}
                              </div>
                              {/* Position Badge */}
                              <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-lg ${
                                item.is_hero 
                                  ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white' 
                                  : 'bg-white/20 backdrop-blur-sm text-white'
                              }`}>
                                {item.position}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )
              })()}

              {/* Detailed View */}
              {viewMode === 'detailed' && (
                <div className="space-y-6">
                  {analysisResults.recommended_order.map((item) => {
                    const imageData = analysisResults.images?.find(img => img.id === item.image_id)
                    if (!imageData) return null

                    // Extract clean filename using helper
                    const displayName = getCleanFilename(imageData.filename)

                    return (
                      <div key={item.image_id} className="card-glass p-6">
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                          {/* Image Column */}
                          <div className="lg:col-span-1">
                            <div className="relative">
                              {/* Position Badge */}
                              <div className="absolute top-3 left-3 z-10">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold ${
                                  item.is_hero 
                                    ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white' 
                                    : 'bg-white/20 backdrop-blur-sm text-white'
                                }`}>
                                  {item.position}
                                </div>
                              </div>
                              {item.is_hero && (
                                <div className="absolute top-3 right-3 z-10">
                                  <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-sm font-bold px-3 py-1 rounded-full">
                                    🏆 HERO
                                  </div>
                                </div>
                              )}
                              
                              <div className="aspect-square bg-gradient-to-br from-dark-800 to-dark-700 rounded-lg overflow-hidden">
                                {imageData.image_url ? (
                                  <img 
                                    src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${imageData.image_url}`}
                                    alt={displayName}
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                      e.target.style.display = 'none'
                                      e.target.parentElement.innerHTML = '<div class="w-full h-full flex flex-col items-center justify-center text-white/40"><svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg><p class="mt-2 text-sm">Image not available</p></div>'
                                    }}
                                  />
                                ) : (
                                  <div className="w-full h-full flex flex-col items-center justify-center text-white/40">
                                    <ImageIcon className="w-16 h-16" />
                                    <p className="mt-2 text-sm">No image URL</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Details Column */}
                          <div className="lg:col-span-2 space-y-4">
                            <div>
                              <h3 className="text-xl font-bold text-white mb-2">{displayName}</h3>
                              <div className="flex items-center space-x-4 text-white/60 text-sm flex-wrap gap-y-1">
                                <span>{imageData.quality_metrics.resolution[0]} x {imageData.quality_metrics.resolution[1]}</span>
                                {imageData.quality_metrics.megapixels && (
                                  <>
                                    <span>•</span>
                                    <span>{imageData.quality_metrics.megapixels.toFixed(1)}MP</span>
                                  </>
                                )}
                                {imageData.quality_metrics.format && imageData.quality_metrics.format !== 'unknown' && (
                                  <>
                                    <span>•</span>
                                    <span>{imageData.quality_metrics.format}</span>
                                  </>
                                )}
                                {imageData.quality_metrics.file_size && imageData.quality_metrics.file_size > 0 && (
                                  <>
                                    <span>•</span>
                                    <span>{(imageData.quality_metrics.file_size / 1024 / 1024).toFixed(2)}MB</span>
                                  </>
                                )}
                                <span>•</span>
                                <span>Position #{item.position}</span>
                              </div>
                            </div>

                            {/* Quality Score with Grade */}
                            <div className="card-glass p-4">
                              <div className="flex items-center justify-between mb-3">
                                <div>
                                  <span className="text-white font-semibold">Overall Quality Score</span>
                                  {imageData.quality_metrics.quality_grade && (
                                    <div className={`inline-block ml-3 px-2 py-1 rounded text-xs font-bold ${
                                      imageData.quality_metrics.quality_grade === 'EXCEPTIONAL' ? 'bg-green-500/20 text-green-300' :
                                      imageData.quality_metrics.quality_grade === 'PROFESSIONAL' ? 'bg-blue-500/20 text-blue-300' :
                                      imageData.quality_metrics.quality_grade === 'GOOD' ? 'bg-cyan-500/20 text-cyan-300' :
                                      imageData.quality_metrics.quality_grade === 'ACCEPTABLE' ? 'bg-yellow-500/20 text-yellow-300' :
                                      'bg-red-500/20 text-red-300'
                                    }`}>
                                      {imageData.quality_metrics.quality_grade}
                                    </div>
                                  )}
                                </div>
                                <span className="text-2xl font-bold text-white">{imageData.quality_metrics.composite_score.toFixed(1)}</span>
                              </div>
                              <div className="w-full bg-white/10 rounded-full h-3">
                                <div 
                                  className="bg-gradient-to-r from-primary-400 to-secondary-400 h-3 rounded-full transition-all duration-500"
                                  style={{ width: `${imageData.quality_metrics.composite_score}%` }}
                                ></div>
                              </div>
                            </div>

                            {/* Technical Metrics - Enhanced */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                              <div className="card-glass p-3">
                                <div className="text-white/60 text-xs mb-1">Sharpness</div>
                                <div className="text-white font-bold">{imageData.quality_metrics.blur_score.toFixed(0)}</div>
                                <div className="text-white/40 text-xs mt-1">
                                  {imageData.quality_metrics.blur_score >= 500 ? '✅ Sharp' : 
                                   imageData.quality_metrics.blur_score >= 300 ? '⚠️ Moderate' : '🚨 Blurry'}
                                </div>
                              </div>
                              <div className="card-glass p-3">
                                <div className="text-white/60 text-xs mb-1">Brightness</div>
                                <div className="text-white font-bold">{imageData.quality_metrics.brightness.toFixed(0)}</div>
                                <div className="text-white/40 text-xs mt-1">
                                  {imageData.quality_metrics.brightness >= 100 && imageData.quality_metrics.brightness <= 150 ? '✅ Perfect' :
                                   imageData.quality_metrics.brightness < 80 ? '🔦 Dark' : 
                                   imageData.quality_metrics.brightness > 170 ? '☀️ Bright' : '⚠️ OK'}
                                </div>
                              </div>
                              <div className="card-glass p-3">
                                <div className="text-white/60 text-xs mb-1">Contrast</div>
                                <div className="text-white font-bold">{imageData.quality_metrics.contrast.toFixed(0)}</div>
                                <div className="text-white/40 text-xs mt-1">
                                  {imageData.quality_metrics.contrast >= 50 ? '✅ Excellent' :
                                   imageData.quality_metrics.contrast >= 35 ? '⚠️ Moderate' : '🎨 Low'}
                                </div>
                              </div>
                              {imageData.quality_metrics.aspect_ratio && (
                                <div className="card-glass p-3">
                                  <div className="text-white/60 text-xs mb-1">Aspect Ratio</div>
                                  <div className="text-white font-bold">{imageData.quality_metrics.aspect_ratio.toFixed(2)}:1</div>
                                  <div className="text-white/40 text-xs mt-1">
                                    {imageData.quality_metrics.aspect_ratio >= 0.95 && imageData.quality_metrics.aspect_ratio <= 1.05 ? '✅ Square' :
                                     imageData.quality_metrics.aspect_ratio >= 1.3 && imageData.quality_metrics.aspect_ratio <= 1.4 ? '✅ 4:3' :
                                     imageData.quality_metrics.aspect_ratio >= 1.7 && imageData.quality_metrics.aspect_ratio <= 1.8 ? '✅ 16:9' :
                                     '⚠️ Custom'}
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Why this position */}
                            <div className="card-glass p-4 bg-primary-500/10 border border-primary-500/20">
                              <div className="text-primary-300 font-semibold mb-2">📊 Position Analysis</div>
                              <p className="text-white/90 leading-relaxed">{item.reason}</p>
                            </div>

                            {/* AI Recommendations */}
                            {imageData.quality_metrics.suggestions && imageData.quality_metrics.suggestions.length > 0 && (
                              <div className="card-glass p-4 bg-yellow-500/10 border border-yellow-500/20">
                                <div className="text-yellow-300 font-semibold mb-3 flex items-center">
                                  <span className="mr-2">💡</span> AI Recommendations
                                </div>
                                <div className="space-y-2">
                                  {imageData.quality_metrics.suggestions.map((suggestion, idx) => (
                                    <div key={idx} className="text-white/90 text-sm leading-relaxed flex">
                                      <span className="text-yellow-400 mr-2">•</span>
                                      <span>{suggestion}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ResultsPage
