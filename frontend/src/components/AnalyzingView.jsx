import React, { useEffect, useState } from 'react'
import { Sparkles, Zap, Image, Brain } from 'lucide-react'

const AnalyzingView = () => {
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState(0)

  const steps = [
    { icon: Image, label: 'Loading images from cloud storage', duration: 1000 },
    { icon: Brain, label: 'Analyzing image quality & composition', duration: 2000 },
    { icon: Zap, label: 'Generating AI embeddings with CLIP', duration: 4000 },
    { icon: Sparkles, label: 'Calculating optimal order & diversity', duration: 1000 }
  ]

  useEffect(() => {
    // Simulate progress through steps
    let stepIndex = 0
    let progressValue = 0
    
    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        progressValue += 2
        if (progressValue >= (stepIndex + 1) * (100 / steps.length)) {
          stepIndex++
          setCurrentStep(stepIndex)
        }
        setProgress(Math.min(progressValue, 95)) // Cap at 95% until real completion
      }
    }, 100)

    return () => clearInterval(interval)
  }, [])

  const StepIcon = currentStep < steps.length ? steps[currentStep].icon : Sparkles

  return (
    <div className="min-h-screen bg-gradient-dark relative overflow-hidden flex items-center justify-center">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '3s' }}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent-purple/10 rounded-full blur-3xl animate-pulse"></div>
      </div>

      <div className="relative z-10 max-w-2xl mx-auto px-4 text-center">
        {/* Main Spinner */}
        <div className="mb-8 relative">
          <div className="relative inline-block">
            {/* Spinning outer ring */}
            <div className="w-32 h-32 rounded-full border-4 border-primary-500/20 border-t-primary-500 animate-spin"></div>
            
            {/* Pulsing inner circle */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-500/30 to-secondary-500/30 backdrop-blur-sm flex items-center justify-center animate-pulse">
                <StepIcon className="w-12 h-12 text-white" />
              </div>
            </div>

            {/* Glow effect */}
            <div className="absolute inset-0 w-32 h-32 bg-primary-400 rounded-full blur-2xl opacity-20 animate-pulse"></div>
          </div>
        </div>

        {/* Title */}
        <h2 className="text-4xl font-bold text-white mb-4 animate-fade-in">
          Analyzing Your Carousel
        </h2>

        {/* Current Step */}
        <div className="mb-8 animate-fade-in">
          <p className="text-xl text-white/80 mb-2">
            {currentStep < steps.length ? steps[currentStep].label : 'Finalizing results...'}
          </p>
          <p className="text-sm text-white/50">
            This may take 8-10 seconds for AI processing
          </p>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden backdrop-blur-sm mb-8">
          <div 
            className="h-full bg-gradient-to-r from-primary-500 to-secondary-500 transition-all duration-300 ease-out rounded-full relative"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute inset-0 bg-white/20 animate-shimmer"></div>
          </div>
        </div>

        {/* Step Indicators */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {steps.map((step, index) => {
            const Icon = step.icon
            const isComplete = index < currentStep
            const isCurrent = index === currentStep
            
            return (
              <div 
                key={index}
                className={`flex flex-col items-center transition-all duration-300 ${
                  isComplete ? 'opacity-100' : isCurrent ? 'opacity-100 scale-110' : 'opacity-40'
                }`}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all duration-300 ${
                  isComplete 
                    ? 'bg-primary-500/30 border-2 border-primary-500' 
                    : isCurrent 
                    ? 'bg-primary-500/20 border-2 border-primary-400 animate-pulse' 
                    : 'bg-white/5 border-2 border-white/10'
                }`}>
                  <Icon className={`w-6 h-6 ${isComplete || isCurrent ? 'text-white' : 'text-white/30'}`} />
                </div>
                <p className={`text-xs text-center ${isComplete || isCurrent ? 'text-white/80' : 'text-white/30'}`}>
                  Step {index + 1}
                </p>
              </div>
            )
          })}
        </div>

        {/* Fun Fact */}
        <div className="card-glass p-4 animate-fade-in">
          <p className="text-sm text-white/60">
            <span className="text-primary-300 font-semibold">💡 Did you know?</span> Our AI uses OpenAI's CLIP model 
            with 151M parameters to understand image semantics and visual similarity.
          </p>
        </div>
      </div>
    </div>
  )
}

export default AnalyzingView
