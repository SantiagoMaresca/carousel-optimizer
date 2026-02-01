import React from 'react'
import { AlertCircle, RefreshCw, Home, Mail } from 'lucide-react'
import useAppStore from '../stores/appStore'

const ErrorPage = ({ error, onRetry }) => {
  const { reset } = useAppStore()

  const handleReset = () => {
    reset()
    if (onRetry) {
      onRetry()
    }
  }

  const handleGoHome = () => {
    reset()
    window.location.href = '/'
  }

  return (
    <div className="min-h-screen bg-gradient-dark relative overflow-hidden flex items-center justify-center">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-500/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-orange-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '3s' }}></div>
      </div>

      <div className="relative z-10 max-w-2xl mx-auto px-4 text-center">
        {/* Error Icon */}
        <div className="mb-8 relative inline-block">
          <div className="relative">
            {/* Pulsing outer ring */}
            <div className="w-32 h-32 rounded-full border-4 border-red-500/20 animate-pulse"></div>
            
            {/* Error circle */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-red-500/30 to-orange-500/30 backdrop-blur-sm flex items-center justify-center">
                <AlertCircle className="w-12 h-12 text-red-400" />
              </div>
            </div>

            {/* Glow effect */}
            <div className="absolute inset-0 w-32 h-32 bg-red-400 rounded-full blur-2xl opacity-20"></div>
          </div>
        </div>

        {/* Title */}
        <h2 className="text-4xl font-bold text-white mb-4 animate-fade-in">
          Oops! Something Went Wrong
        </h2>

        {/* Error Message */}
        <div className="mb-8 animate-fade-in">
          <p className="text-xl text-white/80 mb-4">
            We encountered an issue while processing your request.
          </p>
          
          {error && (
            <div className="card-glass p-4 mb-6 border-l-4 border-red-500">
              <p className="text-sm text-red-300 font-mono text-left">
                {error.message || error.toString()}
              </p>
            </div>
          )}

          <p className="text-sm text-white/60">
            Don't worry—your images are safe. Try again or start over.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
          <button
            onClick={handleReset}
            className="btn-primary flex items-center justify-center space-x-2"
          >
            <RefreshCw className="w-5 h-5" />
            <span>Try Again</span>
          </button>

          <button
            onClick={handleGoHome}
            className="btn-secondary flex items-center justify-center space-x-2"
          >
            <Home className="w-5 h-5" />
            <span>Start Over</span>
          </button>
        </div>

        {/* Help Section */}
        <div className="card-glass p-6 animate-fade-in">
          <h3 className="text-lg font-semibold text-white mb-4">Common Issues & Solutions</h3>
          
          <div className="space-y-3 text-left">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-primary-400 rounded-full mt-2"></div>
              <div>
                <p className="text-white/80 font-medium">File size too large</p>
                <p className="text-sm text-white/60">Keep images under 10MB each</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-primary-400 rounded-full mt-2"></div>
              <div>
                <p className="text-white/80 font-medium">Network timeout</p>
                <p className="text-sm text-white/60">Check your internet connection and try again</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-primary-400 rounded-full mt-2"></div>
              <div>
                <p className="text-white/80 font-medium">Unsupported format</p>
                <p className="text-sm text-white/60">Use JPG, PNG, or WebP images only</p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-white/10">
            <p className="text-sm text-white/60 mb-2">Still having issues?</p>
            <a 
              href="mailto:support@example.com" 
              className="inline-flex items-center space-x-2 text-primary-400 hover:text-primary-300 transition-colors"
            >
              <Mail className="w-4 h-4" />
              <span>Contact Support</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ErrorPage
