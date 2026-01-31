import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, Image as ImageIcon } from 'lucide-react'
import toast from 'react-hot-toast'

const FileDropzone = ({ onFilesSelected, selectedFiles, onRemoveFile, isLoading }) => {
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const errors = rejectedFiles.map(({ file, errors }) => 
        `${file.name}: ${errors.map(e => e.message).join(', ')}`
      )
      toast.error(`Some files were rejected:\n${errors.join('\n')}`)
    }

    // Handle accepted files
    if (acceptedFiles.length > 0) {
      const totalFiles = selectedFiles.length + acceptedFiles.length
      if (totalFiles > 12) {
        toast.error(`Maximum 12 files allowed. You tried to add ${acceptedFiles.length} files to ${selectedFiles.length} existing files.`)
        return
      }

      onFilesSelected(acceptedFiles)
      toast.success(`Added ${acceptedFiles.length} file${acceptedFiles.length > 1 ? 's' : ''}`)
    }
  }, [selectedFiles.length, onFilesSelected])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp']
    },
    maxSize: 8 * 1024 * 1024, // 8MB
    maxFiles: 12,
    disabled: isLoading,
  })

  const getDropzoneClass = () => {
    let baseClass = 'dropzone min-h-64 flex flex-col items-center justify-center space-y-6 relative overflow-hidden'
    if (isDragActive && !isDragReject) {
      baseClass += ' active'
    } else if (isDragReject) {
      baseClass += ' reject'
    }
    if (isLoading) {
      baseClass += ' opacity-50 cursor-not-allowed'
    }
    return baseClass
  }

  return (
    <div className="w-full">
      <div {...getRootProps()} className={getDropzoneClass()}>
        <input {...getInputProps()} />
        
        {/* Animated Upload Icon */}
        <div className="relative">
          <Upload className={`w-16 h-16 transition-all duration-300 ${
            isDragActive ? 'text-primary-400 scale-110' : 'text-white/60'
          }`} />
          {!isDragActive && (
            <div className="absolute inset-0 w-16 h-16 bg-primary-400/20 rounded-full blur-xl animate-pulse"></div>
          )}
        </div>
        
        {/* Dynamic Content */}
        {isDragActive ? (
          <div className="text-center animate-scale-in">
            <p className="text-2xl font-semibold text-white mb-2">Drop the files here!</p>
            <p className="text-white/70">We'll process them instantly</p>
          </div>
        ) : (
          <div className="text-center space-y-4">
            <div>
              <p className="text-2xl font-semibold text-white mb-3">
                Drag & Drop Your Images
              </p>
              <p className="text-white/60 text-lg">
                or click to browse your files
              </p>
            </div>
            
            {/* Enhanced File Info */}
            <div className="bg-white/5 rounded-xl p-4 max-w-md mx-auto backdrop-blur-sm border border-white/10">
              <div className="flex items-center justify-center space-x-6 text-sm text-white/70">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-primary-400 rounded-full"></div>
                  <span>JPG, PNG, WebP</span>
                </div>
                <div className="w-px h-4 bg-white/20"></div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-secondary-400 rounded-full"></div>
                  <span>Max 8MB each</span>
                </div>
                <div className="w-px h-4 bg-white/20"></div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-accent-purple rounded-full"></div>
                  <span>2-12 images</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Decorative Elements */}
        <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-white/20 rounded-tl-lg"></div>
        <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-white/20 rounded-tr-lg"></div>
        <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-white/20 rounded-bl-lg"></div>
        <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-white/20 rounded-br-lg"></div>
      </div>

      {/* Enhanced File Preview Grid */}
      {selectedFiles.length > 0 && (
        <div className="mt-8 animate-slide-up">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <h3 className="text-xl font-semibold text-white">
                Selected Images
              </h3>
              <div className="bg-primary-500/20 text-primary-300 rounded-full px-3 py-1 text-sm font-medium border border-primary-500/30">
                {selectedFiles.length}/12
              </div>
            </div>
            
            {selectedFiles.length >= 2 && (
              <div className="status-success animate-bounce-soft">
                Ready to analyze ✓
              </div>
            )}
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            {selectedFiles.map((file, index) => (
              <FilePreview 
                key={`${file.name}-${index}`} 
                file={file} 
                onRemove={() => onRemoveFile(index)}
                isLoading={isLoading}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const FilePreview = ({ file, onRemove, isLoading }) => {
  const [preview, setPreview] = React.useState(null)

  React.useEffect(() => {
    if (file) {
      const url = URL.createObjectURL(file)
      setPreview(url)
      return () => URL.revokeObjectURL(url)
    }
  }, [file])

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="relative group">
      <div className="card-glass overflow-hidden transition-all duration-300 group-hover:scale-105 group-hover:shadow-xl">
        <div className="aspect-square bg-gradient-to-br from-dark-800 to-dark-700 overflow-hidden relative">
          {preview ? (
            <img
              src={preview}
              alt={file.name}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <ImageIcon className="w-8 h-8 text-white/40" />
            </div>
          )}
          
          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-dark-900/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          
          {/* Remove Button */}
          {!isLoading && (
            <button
              onClick={onRemove}
              className="absolute top-2 right-2 p-2 bg-red-500/90 backdrop-blur-sm text-white rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300 hover:bg-red-600 hover:scale-110 shadow-lg"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          {/* File Info Overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-dark-900/90 to-transparent transform translate-y-full group-hover:translate-y-0 transition-transform duration-300">
            <p className="text-sm font-medium text-white truncate mb-1" title={file.name}>
              {file.name}
            </p>
            <p className="text-xs text-white/60">
              {formatFileSize(file.size)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FileDropzone