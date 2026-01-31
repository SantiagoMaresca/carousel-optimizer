import React from 'react'
import { Loader2, Brain, Search, Sparkles } from 'lucide-react'

const LoadingSpinner = ({ message = 'Processing...', showProgress = false, progress = 0 }) => {
  return (
    <div className="fixed inset-0 bg-dark-900/80 backdrop-blur-md flex items-center justify-center z-50">
      <div className="card-glass p-10 max-w-lg w-full mx-4 text-center animate-scale-in">
        {/* Animated Loading Icon */}
        <div className="relative mb-8">
          <div className="w-20 h-20 mx-auto relative">
            <Loader2 className="w-20 h-20 text-primary-400 animate-spin" />
            <div className="absolute inset-0 w-20 h-20 bg-primary-400/20 rounded-full blur-xl pulse-glow"></div>
          </div>
        </div>
        
        {/* Message */}
        <h3 className="text-2xl font-bold text-white mb-6">{message}</h3>
        
        {/* Progress Bar */}
        {showProgress && (
          <div className="mb-8">
            <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-primary-500 to-secondary-500 h-3 rounded-full transition-all duration-700 ease-out relative"
                style={{ width: `${progress}%` }}
              >
                <div className="absolute inset-0 bg-white/30 shimmer rounded-full"></div>
              </div>
            </div>
            <p className="text-primary-300 font-medium mt-3">{progress}% complete</p>
          </div>
        )}
        
        {/* Processing Steps */}
        <div className="space-y-4 mb-8">
          <div className="flex items-center justify-center space-x-3 text-white/80">
            <Brain className="w-5 h-5 text-primary-400 animate-bounce-soft" />
            <span>Analyzing image quality with AI</span>
          </div>
          <div className="flex items-center justify-center space-x-3 text-white/80" style={{ animationDelay: '1s' }}>
            <Search className="w-5 h-5 text-secondary-400 animate-bounce-soft" />
            <span>Detecting duplicates and similarities</span>
          </div>
          <div className="flex items-center justify-center space-x-3 text-white/80" style={{ animationDelay: '2s' }}>
            <Sparkles className="w-5 h-5 text-accent-purple animate-bounce-soft" />
            <span>Generating smart recommendations</span>
          </div>
        </div>
        
        {/* Time Estimate */}
        <div className="bg-white/5 rounded-xl p-4 border border-white/10">
          <p className="text-white/60 text-sm">
            ⚡ Processing usually takes 5-10 seconds
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoadingSpinner