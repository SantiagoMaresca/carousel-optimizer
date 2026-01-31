import axios from 'axios'
import toast from 'react-hot-toast'
import { apiLogger } from '../utils/logger.js'

// Create axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 120000, // 2 minutes timeout for analysis
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    apiLogger.apiCall(config.method || 'GET', config.url, config.data)
    return config
  },
  (error) => {
    apiLogger.apiError(error, 'Request interceptor')
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    apiLogger.apiResponse(response.status, response.config.url, response.data)
    return response
  },
  (error) => {
    apiLogger.apiError(error, 'Response interceptor')
    
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.error || error.response.data?.detail || 'Server error'
      toast.error(`Error: ${message}`)
    } else if (error.request) {
      // Request was made but no response received
      toast.error('Network error: Please check your connection')
    } else {
      // Something happened in setting up the request
      toast.error(`Request error: ${error.message}`)
    }
    
    return Promise.reject(error)
  }
)

// API methods
export const apiService = {
  // Health check
  async health() {
    const response = await api.get('/health')
    return response.data
  },

  // Upload files
  async uploadFiles(files) {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })

    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 1 minute for upload
    })

    return response.data
  },

  // Analyze images
  async analyzeImages(sessionId, duplicateThreshold = 0.92) {
    const response = await api.post('/api/analyze', {
      session_id: sessionId,
      duplicate_threshold: duplicateThreshold,
    })

    return response.data
  },

  // Get session info
  async getSessionInfo(sessionId) {
    const response = await api.get(`/api/session/${sessionId}`)
    return response.data
  },
}

export default api