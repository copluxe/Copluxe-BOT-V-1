import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import clsx from 'clsx'

const MAX_PHOTOS = 10
const MIN_PHOTOS = 3

export default function PhotoUploader({ photos, onPhotosChange }) {
  const [error, setError] = useState('')

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError('')

    if (rejectedFiles.length > 0) {
      setError('Certains fichiers ont été refusés. Seuls JPG, PNG et WebP sont acceptés.')
    }

    const remaining = MAX_PHOTOS - photos.length
    const filesToAdd = acceptedFiles.slice(0, remaining)

    const newPhotos = filesToAdd.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      id: Math.random().toString(36).slice(2),
    }))

    onPhotosChange([...photos, ...newPhotos])

    if (acceptedFiles.length > remaining) {
      setError(`Maximum ${MAX_PHOTOS} photos. ${acceptedFiles.length - remaining} photo(s) ignorée(s).`)
    }
  }, [photos, onPhotosChange])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
    disabled: photos.length >= MAX_PHOTOS,
    multiple: true,
  })

  function removePhoto(id) {
    const photo = photos.find(p => p.id === id)
    if (photo?.preview) URL.revokeObjectURL(photo.preview)
    onPhotosChange(photos.filter(p => p.id !== id))
  }

  const canAdd = photos.length < MAX_PHOTOS

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      {canAdd && (
        <div
          {...getRootProps()}
          className={clsx(
            'border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200',
            isDragActive
              ? 'border-brand-purple bg-brand-purple/10 drag-active'
              : 'border-white/15 hover:border-brand-purple/50 hover:bg-white/3'
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center">
              <svg className="w-7 h-7 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            {isDragActive ? (
              <p className="text-brand-violet font-medium">Dépose tes photos ici ✨</p>
            ) : (
              <>
                <p className="text-white/70 font-medium">
                  Glisse tes photos ici ou <span className="text-brand-violet">clique pour choisir</span>
                </p>
                <p className="text-white/30 text-sm">
                  {MIN_PHOTOS}–{MAX_PHOTOS} photos • JPG, PNG, WebP • Max 50MB chacune
                </p>
              </>
            )}
            <div className="flex gap-2 mt-1">
              <span className={clsx(
                'text-xs px-3 py-1 rounded-full',
                photos.length >= MIN_PHOTOS ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/40'
              )}>
                {photos.length}/{MIN_PHOTOS} minimum
              </span>
              <span className="text-xs px-3 py-1 rounded-full bg-white/10 text-white/40">
                {photos.length}/{MAX_PHOTOS} max
              </span>
            </div>
          </div>
        </div>
      )}

      {error && (
        <p className="text-amber-400 text-sm bg-amber-400/10 rounded-xl px-4 py-2">{error}</p>
      )}

      {/* Photo grid */}
      {photos.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
          {photos.map((photo, index) => (
            <div key={photo.id} className="relative group aspect-tiktok rounded-xl overflow-hidden">
              <img
                src={photo.preview}
                alt={`Photo ${index + 1}`}
                className="w-full h-full object-cover"
              />
              {/* Overlay */}
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button
                  onClick={() => removePhoto(photo.id)}
                  className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                >
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              {/* Order number */}
              <div className="absolute top-1.5 left-1.5 w-5 h-5 bg-black/60 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">{index + 1}</span>
              </div>
            </div>
          ))}

          {/* Add more button */}
          {canAdd && (
            <div
              {...getRootProps()}
              className="aspect-tiktok rounded-xl border-2 border-dashed border-white/15 hover:border-brand-purple/50 cursor-pointer flex items-center justify-center transition-colors hover:bg-white/3"
            >
              <input {...getInputProps()} />
              <svg className="w-8 h-8 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
              </svg>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
