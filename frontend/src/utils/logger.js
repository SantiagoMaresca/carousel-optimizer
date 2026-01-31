/**
 * Frontend logging utility with different log levels
 */

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
}

const LOG_LEVEL = import.meta.env.PROD ? LOG_LEVELS.WARN : LOG_LEVELS.DEBUG

class Logger {
  constructor(context = 'App') {
    this.context = context
  }

  formatMessage(level, message, ...args) {
    const timestamp = new Date().toISOString()
    const prefix = `[${timestamp}] [${this.context}] [${level}]`
    
    if (args.length > 0) {
      return [prefix, message, ...args]
    }
    return [prefix, message]
  }

  debug(message, ...args) {
    if (LOG_LEVEL <= LOG_LEVELS.DEBUG) {
      console.log(...this.formatMessage('DEBUG', message, ...args))
    }
  }

  info(message, ...args) {
    if (LOG_LEVEL <= LOG_LEVELS.INFO) {
      console.info(...this.formatMessage('INFO', message, ...args))
    }
  }

  warn(message, ...args) {
    if (LOG_LEVEL <= LOG_LEVELS.WARN) {
      console.warn(...this.formatMessage('WARN', message, ...args))
    }
  }

  error(message, ...args) {
    if (LOG_LEVEL <= LOG_LEVELS.ERROR) {
      console.error(...this.formatMessage('ERROR', message, ...args))
    }
  }

  // Special methods for specific contexts
  apiCall(method, url, data = null) {
    this.debug(`API ${method.toUpperCase()} ${url}`, data ? { data } : '')
  }

  apiResponse(status, url, data = null) {
    this.debug(`API Response ${status} ${url}`, data ? { data } : '')
  }

  apiError(error, context = '') {
    this.error(`API Error ${context}:`, error)
  }

  userAction(action, details = null) {
    this.info(`User Action: ${action}`, details ? { details } : '')
  }

  fileUpload(filename, size) {
    this.info(`File Upload: ${filename} (${size} bytes)`)
  }

  analysisStart(sessionId, fileCount) {
    this.info(`Analysis Started: session ${sessionId}, ${fileCount} files`)
  }

  analysisComplete(sessionId, duration) {
    this.info(`Analysis Complete: session ${sessionId}, ${duration}ms`)
  }
}

// Create default logger instances
export const logger = new Logger('App')
export const apiLogger = new Logger('API')
export const uiLogger = new Logger('UI')
export const uploadLogger = new Logger('Upload')

export default Logger